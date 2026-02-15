from decimal import Decimal
from django.db import models
from rest_framework import serializers
from .models import CategoryMain, CategorySub, Receipt, ReceiptImage, ReceiptItem


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def _get_or_create_categories(main_name: str | None, sub_name: str | None) -> tuple[CategoryMain | None, CategorySub | None]:
    main = None
    sub = None
    main_name = _normalize_text(main_name or "")
    sub_name = _normalize_text(sub_name or "")
    if main_name:
        main, _ = CategoryMain.objects.get_or_create(name=main_name)
        if sub_name:
            sub, _ = CategorySub.objects.get_or_create(main=main, name=sub_name)
    return main, sub


class ReceiptImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptImage
        fields = ["id", "image", "order"]


class ReceiptItemSerializer(serializers.ModelSerializer):
    main_category = serializers.CharField(required=False, allow_blank=True)
    sub_category = serializers.CharField(required=False, allow_blank=True)
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
            "total_price",
            "tags",
            "confidence",
            "line_index",
            "main_category",
            "sub_category",
            "target_org_id",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["main_category"] = instance.category_main.name if instance.category_main else ""
        data["sub_category"] = instance.category_sub.name if instance.category_sub else ""
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
                sub_name = item.pop("sub_category", "")
                line_index = item.pop("line_index", index)
                category_main, category_sub = _get_or_create_categories(main_name, sub_name)
                ReceiptItem.objects.create(
                    receipt=instance,
                    category_main=category_main,
                    category_sub=category_sub,
                    line_index=line_index,
                    **item,
                )

            if instance.total is None:
                total = instance.items.aggregate(total=models.Sum("total_price"))["total"]
                if total is not None:
                    instance.total = Decimal(total)
                    instance.save(update_fields=["total"])

        return instance
