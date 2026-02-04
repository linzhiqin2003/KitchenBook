from decimal import Decimal
from datetime import date, timedelta

import json

from django.conf import settings
from django.db import models, transaction
from django.db.models import Value
from django.db.models.functions import TruncDate, TruncMonth, Coalesce
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from accounts.models import OrganizationMember
from .models import CategoryMain, CategorySub, Receipt, ReceiptItem
from .serializers import ReceiptSerializer
from .services.doubao import analyze_receipt, analyze_receipt_stream
from .services.parsing import NotReceiptError, parse_receipt_payload, parse_datetime_with_tz, to_decimal


def get_active_org_id(request):
    """Read X-Active-Org header and validate membership. Returns org UUID or None."""
    org_id = request.headers.get("X-Active-Org", "").strip()
    if not org_id:
        return None
    if request.user and request.user.is_authenticated:
        if OrganizationMember.objects.filter(org_id=org_id, user=request.user).exists():
            return org_id
    return None


def _get_payer_default(request):
    """Return default payer name from user profile."""
    if request.user and request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if profile and profile.nickname:
            return profile.nickname
    return ""


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def _get_or_create_categories(main_name: str | None, sub_name: str | None):
    main = None
    sub = None
    main_name = _normalize_text(main_name or "")
    sub_name = _normalize_text(sub_name or "")
    if main_name:
        main, _ = CategoryMain.objects.get_or_create(name=main_name)
        if sub_name:
            sub, _ = CategorySub.objects.get_or_create(main=main, name=sub_name)
    return main, sub


MERCHANT_ALIASES = {
    "朗御": "LANGYU",
}

_Q2 = Decimal("0.01")


def _prorate_decimal(value, ratio):
    """按比例分摊一个 Decimal 值，保留 2 位小数。None 保持 None。"""
    if value is None:
        return None
    return (Decimal(str(value)) * ratio).quantize(_Q2)


def _calc_total(subtotal, tax, discount):
    """total = subtotal + tax - discount（None 视作 0）。"""
    return (subtotal or Decimal("0")) + (tax or Decimal("0")) - (discount or Decimal("0"))


def _apply_prorated_financials(receipt_obj, subtotal, tax, discount):
    """将分摊后的 subtotal/tax/discount 写入 receipt 并计算 total。"""
    receipt_obj.subtotal = subtotal
    receipt_obj.tax = tax
    receipt_obj.discount = discount
    receipt_obj.total = _calc_total(subtotal, tax, discount)


@transaction.atomic
def _apply_parsed_result(receipt: Receipt, parsed, raw_text: str, raw_json: dict):
    payload = parsed.receipt
    receipt.raw_model_output = raw_text
    receipt.raw_model_json = raw_json
    merchant = payload.merchant or receipt.merchant
    receipt.merchant = MERCHANT_ALIASES.get(merchant, merchant)
    receipt.address = payload.address or receipt.address
    receipt.currency = payload.currency or receipt.currency

    parsed_dt = parse_datetime_with_tz(payload.purchased_at)
    if parsed_dt:
        receipt.purchased_at = parsed_dt
    elif receipt.purchased_at is None:
        receipt.purchased_at = timezone.now()

    receipt.subtotal = to_decimal(payload.subtotal)
    receipt.tax = to_decimal(payload.tax)
    receipt.discount = to_decimal(payload.discount)
    receipt.total = to_decimal(payload.total)

    receipt.items.all().delete()
    for index, item in enumerate(payload.items):
        category_main, category_sub = _get_or_create_categories(item.main_category, item.sub_category)
        total_price = to_decimal(item.total_price)
        unit_price = to_decimal(item.unit_price)
        if total_price is None and unit_price is not None:
            quantity = Decimal(str(item.quantity or 1))
            total_price = unit_price * quantity

        ReceiptItem.objects.create(
            receipt=receipt,
            category_main=category_main,
            category_sub=category_sub,
            name=item.name,
            brand=item.brand or "",
            quantity=Decimal(str(item.quantity or 1)),
            unit=item.unit or "",
            unit_price=unit_price,
            total_price=total_price,
            tags=item.tags or [],
            confidence=to_decimal(item.confidence),
            line_index=index,
        )

    if receipt.total is None:
        total = receipt.items.aggregate(total=models.Sum("total_price"))["total"]
        receipt.total = total or Decimal("0")

    receipt.status = Receipt.STATUS_READY
    receipt.save()


class ReceiptViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ReceiptSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _check_owner(self, receipt):
        """Raise 403 if the current user is not the receipt owner."""
        if receipt.user_id and receipt.user_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("只能修改自己上传的收据")

    def update(self, request, *args, **kwargs):
        self._check_owner(self.get_object())
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._check_owner(self.get_object())
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._check_owner(self.get_object())
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        qs = Receipt.objects.all().prefetch_related(
            "items", "items__category_main", "items__category_sub"
        ).order_by("-created_at")

        # Data scoping: org mode vs personal mode
        if self.request.user and self.request.user.is_authenticated:
            org_id = get_active_org_id(self.request)
            if org_id:
                qs = qs.filter(organization_id=org_id)
            else:
                qs = qs.filter(user=self.request.user, organization__isnull=True)
        else:
            return qs.none()

        # 列表接口排除失败和处理中的账单；详情接口不限
        if self.action == "list":
            qs = qs.exclude(status__in=[Receipt.STATUS_FAILED, Receipt.STATUS_PROCESSING])
        return qs

    def _set_ownership(self, receipt, request):
        """Set user, organization, and payer on a receipt."""
        if request.user and request.user.is_authenticated:
            receipt.user = request.user
            org_id = get_active_org_id(request)
            if org_id:
                receipt.organization_id = org_id
            payer = request.data.get("payer", "").strip()
            receipt.payer = payer or _get_payer_default(request)

    def create(self, request, *args, **kwargs):
        image = request.FILES.get("image")

        # 无图片 + JSON 请求：手动创建空账单
        if not image and request.content_type and "json" in request.content_type:
            default_currency = getattr(settings, "DEFAULT_CURRENCY", "GBP")
            receipt = Receipt.objects.create(
                merchant=request.data.get("merchant", ""),
                address=request.data.get("address", ""),
                currency=request.data.get("currency", default_currency),
                notes=request.data.get("notes", ""),
                status=Receipt.STATUS_READY,
            )
            self._set_ownership(receipt, request)
            receipt.save()
            serializer = self.get_serializer(receipt)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not image:
            return Response({"detail": "image is required"}, status=status.HTTP_400_BAD_REQUEST)

        receipt = Receipt.objects.create(
            image=image,
            status=Receipt.STATUS_PROCESSING,
            currency=getattr(settings, "DEFAULT_CURRENCY", "GBP"),
        )
        self._set_ownership(receipt, request)
        receipt.save()

        try:
            raw_text, raw_json = analyze_receipt(receipt.image.path)
            parsed = parse_receipt_payload(raw_text)
            _apply_parsed_result(receipt, parsed, raw_text, raw_json)
        except NotReceiptError as exc:
            receipt.delete()
            return Response(
                {"detail": exc.reason, "not_receipt": True},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:  # pragma: no cover - keep error message for UI
            receipt.status = Receipt.STATUS_FAILED
            receipt.raw_model_output = str(exc)
            receipt.save(update_fields=["status", "raw_model_output"])

        serializer = self.get_serializer(receipt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="upload-stream")
    def upload_stream(self, request):
        """SSE endpoint: upload image + stream thinking/generating phases."""
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "image is required"}, status=status.HTTP_400_BAD_REQUEST)

        receipt = Receipt.objects.create(
            image=image,
            status=Receipt.STATUS_PROCESSING,
            currency=getattr(settings, "DEFAULT_CURRENCY", "GBP"),
        )
        self._set_ownership(receipt, request)
        receipt.save()

        def event_stream():
            def sse(data):
                return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            try:
                for event in analyze_receipt_stream(receipt.image.path):
                    phase = event["phase"]
                    if phase in ("thinking", "generating"):
                        yield sse({"phase": phase})
                    elif phase == "done":
                        raw_text = event["content"]
                        try:
                            parsed = parse_receipt_payload(raw_text)
                            _apply_parsed_result(receipt, parsed, raw_text, {})
                        except NotReceiptError as exc:
                            receipt.delete()
                            yield sse({"phase": "error", "detail": exc.reason, "not_receipt": True})
                            return
                        serializer = self.get_serializer(receipt)
                        yield sse({"phase": "done", "receipt": serializer.data})
            except Exception as exc:
                receipt.status = Receipt.STATUS_FAILED
                receipt.raw_model_output = str(exc)
                receipt.save(update_fields=["status", "raw_model_output"])
                serializer = self.get_serializer(receipt)
                yield sse({"phase": "done", "receipt": serializer.data})

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        receipt = self.get_object()
        self._check_owner(receipt)

        # 重复收据检测
        if (
            receipt.merchant
            and receipt.purchased_at
            and receipt.total is not None
            and not request.data.get("force")
        ):
            dup_qs = Receipt.objects.filter(
                user=receipt.user,
                status=Receipt.STATUS_CONFIRMED,
                merchant__iexact=receipt.merchant,
                purchased_at__date=receipt.purchased_at.date(),
                total=receipt.total,
            ).exclude(id=receipt.id)

            if receipt.organization:
                dup_qs = dup_qs.filter(organization=receipt.organization)
            else:
                dup_qs = dup_qs.filter(organization__isnull=True)

            dup = dup_qs.first()
            if dup:
                return Response(
                    {
                        "detail": "检测到重复收据",
                        "duplicate": {
                            "id": str(dup.id),
                            "merchant": dup.merchant,
                            "date": dup.purchased_at.isoformat() if dup.purchased_at else None,
                            "total": str(dup.total),
                        },
                    },
                    status=status.HTTP_409_CONFLICT,
                )

        item_orgs = request.data.get("item_orgs")
        if not item_orgs:
            # Simple confirm — no split
            receipt.status = Receipt.STATUS_CONFIRMED
            if receipt.image:
                self._archive_image(receipt)
            receipt.save(update_fields=["status", "image"])
            return Response(ReceiptSerializer(receipt).data)

        # --- Split confirm: group items by target org ---
        all_items = list(receipt.items.all().order_by("line_index"))

        # Validate membership for all target orgs
        target_org_ids = set()
        for idx_str, org_id in item_orgs.items():
            if org_id:
                target_org_ids.add(org_id)
        for org_id in target_org_ids:
            if not OrganizationMember.objects.filter(org_id=org_id, user=request.user).exists():
                return Response({"detail": f"您不是组织 {org_id} 的成员"}, status=status.HTTP_403_FORBIDDEN)

        current_org_id = str(receipt.organization_id) if receipt.organization_id else ""

        # Snapshot original financials for proportional split
        orig_item_sum = sum((it.total_price or Decimal("0")) for it in all_items)
        orig_subtotal = receipt.subtotal or orig_item_sum
        orig_tax = receipt.tax
        orig_discount = receipt.discount

        # Group items by target org
        groups = {}  # org_id_str -> [item]
        for idx, item in enumerate(all_items):
            target = item_orgs.get(str(idx), current_org_id)
            if target is None:
                target = ""
            groups.setdefault(target, []).append(item)

        with transaction.atomic():
            created_receipts = []
            # Track allocated amounts; remainder goes to current-org group
            allocated_subtotal = Decimal("0")
            allocated_tax = Decimal("0")
            allocated_discount = Decimal("0")

            for org_key, group_items in groups.items():
                if org_key == current_org_id:
                    continue  # handle last

                group_item_sum = sum((it.total_price or Decimal("0")) for it in group_items)
                ratio = (group_item_sum / orig_item_sum) if orig_item_sum else Decimal("0")

                g_subtotal = _prorate_decimal(orig_subtotal, ratio) or Decimal("0")
                g_tax = _prorate_decimal(orig_tax, ratio)
                g_discount = _prorate_decimal(orig_discount, ratio)

                allocated_subtotal += g_subtotal
                allocated_tax += g_tax or Decimal("0")
                allocated_discount += g_discount or Decimal("0")

                new_receipt = Receipt.objects.create(
                    user=receipt.user,
                    organization_id=org_key if org_key else None,
                    merchant=receipt.merchant,
                    address=receipt.address,
                    purchased_at=receipt.purchased_at,
                    currency=receipt.currency,
                    payer=receipt.payer,
                    notes=receipt.notes,
                    status=Receipt.STATUS_CONFIRMED,
                )
                for new_idx, item in enumerate(group_items):
                    item.receipt = new_receipt
                    item.line_index = new_idx
                    item.save(update_fields=["receipt_id", "line_index"])

                _apply_prorated_financials(new_receipt, g_subtotal, g_tax, g_discount)
                new_receipt.save(update_fields=["subtotal", "tax", "discount", "total"])
                created_receipts.append(new_receipt)

            # Current-org group gets the remainder (avoids rounding drift)
            remaining = groups.get(current_org_id, [])
            if remaining:
                for new_idx, item in enumerate(remaining):
                    if item.line_index != new_idx:
                        item.line_index = new_idx
                        item.save(update_fields=["line_index"])

                r_subtotal = orig_subtotal - allocated_subtotal
                r_tax = (orig_tax - allocated_tax) if orig_tax is not None else None
                r_discount = (orig_discount - allocated_discount) if orig_discount is not None else None
                _apply_prorated_financials(receipt, r_subtotal, r_tax, r_discount)

                receipt.status = Receipt.STATUS_CONFIRMED
                if receipt.image:
                    self._archive_image(receipt)
                receipt.save(update_fields=["status", "image", "subtotal", "tax", "discount", "total"])
            else:
                receipt.delete()
                if created_receipts:
                    return Response(ReceiptSerializer(created_receipts[0]).data)
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(ReceiptSerializer(receipt).data)

    @action(detail=True, methods=["post"], url_path="move-items")
    def move_items(self, request, pk=None):
        """Move items between receipts after confirmation, with proportional financials."""
        receipt = self.get_object()
        self._check_owner(receipt)

        moves = request.data.get("moves", [])
        if not moves:
            return Response({"detail": "moves 参数为空"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate membership
        target_org_ids = set()
        for m in moves:
            org_id = m.get("target_org_id")
            if org_id:
                target_org_ids.add(org_id)
        for org_id in target_org_ids:
            if not OrganizationMember.objects.filter(org_id=org_id, user=request.user).exists():
                return Response({"detail": f"您不是组织 {org_id} 的成员"}, status=status.HTTP_403_FORBIDDEN)

        # Snapshot source financials BEFORE any moves
        orig_source_item_sum = receipt.items.aggregate(t=models.Sum("total_price"))["t"] or Decimal("0")
        orig_source_subtotal = receipt.subtotal or orig_source_item_sum
        orig_source_tax = receipt.tax
        orig_source_discount = receipt.discount

        with transaction.atomic():
            # Track: target_receipt_id -> sum of moved items' total_price
            moved_sums_per_target = {}
            affected_receipts = {}  # id -> receipt obj

            for m in moves:
                item_id = m.get("item_id")
                target_org_id = m.get("target_org_id")  # "" or None → personal

                try:
                    item = ReceiptItem.objects.get(id=item_id, receipt=receipt)
                except ReceiptItem.DoesNotExist:
                    continue

                target_org = target_org_id if target_org_id else None
                target_receipt = Receipt.objects.filter(
                    user=receipt.user,
                    organization_id=target_org,
                    merchant=receipt.merchant,
                    purchased_at=receipt.purchased_at,
                    status=Receipt.STATUS_CONFIRMED,
                ).first()

                if not target_receipt:
                    target_receipt = Receipt.objects.create(
                        user=receipt.user,
                        organization_id=target_org,
                        merchant=receipt.merchant,
                        address=receipt.address,
                        purchased_at=receipt.purchased_at,
                        currency=receipt.currency,
                        payer=receipt.payer,
                        notes=receipt.notes,
                        status=Receipt.STATUS_CONFIRMED,
                        subtotal=Decimal("0"),
                        total=Decimal("0"),
                    )

                item_price = item.total_price or Decimal("0")
                max_idx = target_receipt.items.aggregate(m=models.Max("line_index"))["m"]
                item.receipt = target_receipt
                item.line_index = (max_idx or -1) + 1
                item.save(update_fields=["receipt_id", "line_index"])

                tid = target_receipt.id
                moved_sums_per_target[tid] = moved_sums_per_target.get(tid, Decimal("0")) + item_price
                affected_receipts[tid] = target_receipt

            # Proportionally distribute tax/discount to each target
            total_allocated_subtotal = Decimal("0")
            total_allocated_tax = Decimal("0")
            total_allocated_discount = Decimal("0")

            for tid, moved_sum in moved_sums_per_target.items():
                target_r = affected_receipts[tid]
                target_r.refresh_from_db()

                if orig_source_item_sum and orig_source_item_sum > 0:
                    ratio = moved_sum / orig_source_item_sum
                    moved_subtotal = _prorate_decimal(orig_source_subtotal, ratio) or Decimal("0")
                    moved_tax = _prorate_decimal(orig_source_tax, ratio)
                    moved_discount = _prorate_decimal(orig_source_discount, ratio)
                else:
                    moved_subtotal = moved_sum
                    moved_tax = None
                    moved_discount = None

                total_allocated_subtotal += moved_subtotal
                total_allocated_tax += moved_tax or Decimal("0")
                total_allocated_discount += moved_discount or Decimal("0")

                # Add to target's existing financials
                target_r.subtotal = (target_r.subtotal or Decimal("0")) + moved_subtotal
                target_r.tax = (target_r.tax or Decimal("0")) + moved_tax if moved_tax is not None else target_r.tax
                target_r.discount = (target_r.discount or Decimal("0")) + moved_discount if moved_discount is not None else target_r.discount
                target_r.total = _calc_total(target_r.subtotal, target_r.tax, target_r.discount)
                target_r.save(update_fields=["subtotal", "tax", "discount", "total"])

            # Source receipt: subtract moved portion (remainder stays)
            remaining_count = receipt.items.count()
            if remaining_count == 0:
                receipt_id = receipt.id
                receipt.delete()
                return Response({"detail": "原收据已清空并删除", "deleted": True, "id": str(receipt_id)})
            else:
                receipt.subtotal = orig_source_subtotal - total_allocated_subtotal
                receipt.tax = (orig_source_tax - total_allocated_tax) if orig_source_tax is not None else None
                receipt.discount = (orig_source_discount - total_allocated_discount) if orig_source_discount is not None else None
                receipt.total = _calc_total(receipt.subtotal, receipt.tax, receipt.discount)
                receipt.save(update_fields=["subtotal", "tax", "discount", "total"])

        receipt.refresh_from_db()
        return Response(ReceiptSerializer(receipt).data)

    @staticmethod
    def _archive_image(receipt):
        import os
        import re
        from pathlib import Path
        from django.conf import settings

        old_path = Path(receipt.image.path)
        if not old_path.exists():
            return

        ext = old_path.suffix.lower() or ".jpg"

        # 日期部分
        if receipt.purchased_at:
            date_str = receipt.purchased_at.strftime("%Y%m%d")
        else:
            date_str = receipt.created_at.strftime("%Y%m%d")

        # 店名：去除文件名不安全字符，空白转下划线
        merchant = (receipt.merchant or "unknown").strip()
        merchant = re.sub(r'[\\/:*?"<>|]', "", merchant)
        merchant = re.sub(r'\s+', "_", merchant)
        if not merchant:
            merchant = "unknown"

        # 金额
        total_str = f"{receipt.total:.2f}" if receipt.total is not None else "0.00"

        new_name = f"{date_str}_{merchant}_{total_str}{ext}"

        # 归档目录: media/receipts/archived/
        archive_dir = Path(settings.MEDIA_ROOT) / "receipts" / "archived"
        archive_dir.mkdir(parents=True, exist_ok=True)
        new_path = archive_dir / new_name

        # 重名处理
        counter = 1
        stem = new_path.stem
        while new_path.exists():
            new_path = archive_dir / f"{stem}_{counter}{ext}"
            counter += 1

        os.rename(str(old_path), str(new_path))

        # 更新 image 字段为相对于 MEDIA_ROOT 的路径
        receipt.image.name = str(new_path.relative_to(Path(settings.MEDIA_ROOT)))


class StatsOverviewView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        receipts = Receipt.objects.exclude(status=Receipt.STATUS_FAILED)

        # Data scoping
        if request.user and request.user.is_authenticated:
            org_id = get_active_org_id(request)
            if org_id:
                receipts = receipts.filter(organization_id=org_id)
            else:
                receipts = receipts.filter(user=request.user, organization__isnull=True)
        else:
            receipts = receipts.none()

        # 解析时间范围参数
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        date_filter = {}
        if start_date_str:
            try:
                start = date.fromisoformat(start_date_str)
                date_filter["purchased_at__date__gte"] = start
            except ValueError:
                pass
        if end_date_str:
            try:
                end = date.fromisoformat(end_date_str)
                date_filter["purchased_at__date__lte"] = end
            except ValueError:
                pass

        if date_filter:
            receipts = receipts.filter(**date_filter)

        totals = receipts.aggregate(
            total_spend=Coalesce(models.Sum("total"), Decimal("0")),
            receipt_count=Coalesce(models.Count("id"), 0),
        )

        items_qs = ReceiptItem.objects.filter(receipt__in=receipts)

        by_category = (
            items_qs.select_related("category_main")
            .values("category_main__name")
            .annotate(total=Coalesce(models.Sum("total_price"), Decimal("0")))
            .order_by("-total")
        )

        by_month = (
            receipts.annotate(month=TruncMonth("purchased_at"))
            .values("month")
            .annotate(total=Coalesce(models.Sum("total"), Decimal("0")))
            .order_by("month")
        )

        by_day = (
            receipts
            .annotate(day=TruncDate("purchased_at"))
            .values("day")
            .annotate(total=Coalesce(models.Sum("total"), Decimal("0")))
            .order_by("day")
        )

        by_merchant = (
            receipts
            .annotate(
                merchant_name=Coalesce(
                    models.Case(
                        models.When(merchant="", then=Value("未知店铺")),
                        default=models.F("merchant"),
                        output_field=models.CharField(),
                    ),
                    Value("未知店铺"),
                )
            )
            .values("merchant_name")
            .annotate(
                total=Coalesce(models.Sum("total"), Decimal("0")),
                count=models.Count("id"),
            )
            .order_by("-total")
        )

        recent_items = (
            items_qs
            .annotate(
                purchased_at=models.F("receipt__purchased_at"),
                merchant=models.F("receipt__merchant"),
            )
            .order_by("-purchased_at")
            .values("name", "brand", "unit", "category_main__name",
                    "quantity", "total_price", "purchased_at", "merchant")
            [:100]
        )

        data = {
            "total_spend": totals["total_spend"],
            "receipt_count": totals["receipt_count"],
            "by_category": list(by_category),
            "by_month": list(by_month),
            "by_day": list(by_day),
            "by_merchant": list(by_merchant),
            "recent_items": list(recent_items),
        }

        # by_payer aggregation (only in org mode)
        if org_id:
            by_payer = (
                receipts
                .annotate(
                    payer_name=Coalesce(
                        models.Case(
                            models.When(payer="", then=Value("未指定")),
                            default=models.F("payer"),
                            output_field=models.CharField(),
                        ),
                        Value("未指定"),
                    )
                )
                .values("payer_name")
                .annotate(
                    total=Coalesce(models.Sum("total"), Decimal("0")),
                    count=models.Count("id"),
                )
                .order_by("-total")
            )
            data["by_payer"] = list(by_payer)

        return Response(data)
