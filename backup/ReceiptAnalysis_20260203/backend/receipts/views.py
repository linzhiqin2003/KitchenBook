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
        receipt.status = Receipt.STATUS_CONFIRMED

        # 归档重命名图片: {日期}_{店名}_{金额}.ext
        if receipt.image:
            self._archive_image(receipt)

        receipt.save(update_fields=["status", "image"])
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
