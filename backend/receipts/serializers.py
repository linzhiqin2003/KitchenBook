from decimal import Decimal
from django.db import models
from rest_framework import serializers
from .models import CategoryMain, Receipt, ReceiptImage, ReceiptItem


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def _get_or_create_main_category(main_name: str | None) -> CategoryMain | None:
    main_name = _normalize_text(main_name or "")
    if not main_name:
        return None
    main, _ = CategoryMain.objects.get_or_create(name=main_name)
    return main


class ReceiptImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptImage
        fields = ["id", "image", "order"]


class ReceiptItemSerializer(serializers.ModelSerializer):
    main_category = serializers.CharField(required=False, allow_blank=True)
    target_org_id = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = ReceiptItem
        fields = [
            "id",
            "name",
            "brand",
            "quantity",
            "unit",
            "unit_price",
            "discount",
            "total_price",
            "tags",
            "confidence",
            "line_index",
            "main_category",
            "target_org_id",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["main_category"] = instance.category_main.name if instance.category_main else ""
        data.pop("target_org_id", None)
        return data


class ReceiptSerializer(serializers.ModelSerializer):
    items = ReceiptItemSerializer(many=True, required=False)
    images = ReceiptImageSerializer(many=True, read_only=True)
    uploader_name = serializers.SerializerMethodField()
    organization_id = serializers.UUIDField(source="organization.id", read_only=True, default=None)
    organization_name = serializers.CharField(source="organization.name", read_only=True, default="")

    class Meta:
        model = Receipt
        fields = [
            "id",
            "user_id",
            "organization_id",
            "organization_name",
            "merchant",
            "address",
            "purchased_at",
            "currency",
            "subtotal",
            "tax",
            "discount",
            "total",
            "status",
            "image",
            "raw_model_output",
            "raw_model_json",
            "notes",
            "payer",
            "uploader_name",
            "created_at",
            "updated_at",
            "items",
            "images",
        ]
        read_only_fields = ["user_id", "status", "image", "raw_model_output", "raw_model_json", "created_at", "updated_at"]

    def get_uploader_name(self, obj):
        if obj.user:
            profile = getattr(obj.user, "profile", None)
            return profile.nickname if profile else obj.user.username
        return ""

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for index, item in enumerate(items_data):
                item.pop("target_org_id", None)
                main_name = item.pop("main_category", "")
                line_index = item.pop("line_index", index)
                category_main = _get_or_create_main_category(main_name)
                # 自动计算 total_price = unit_price * quantity - discount
                unit_price = item.get("unit_price")
                quantity = item.get("quantity") or Decimal("1")
                discount = item.get("discount") or Decimal("0")
                if unit_price is not None:
                    item["total_price"] = (
                        Decimal(str(unit_price)) * Decimal(str(quantity))
                        - Decimal(str(discount))
                    ).quantize(Decimal("0.01"))
                ReceiptItem.objects.create(
                    receipt=instance,
                    category_main=category_main,
                    line_index=line_index,
                    **item,
                )

            if instance.total is None:
                total = instance.items.aggregate(total=models.Sum("total_price"))["total"]
                if total is not None:
                    instance.total = Decimal(total)
                    instance.save(update_fields=["total"])

        return instance
