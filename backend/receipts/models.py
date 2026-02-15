import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models


class CategoryMain(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class CategorySub(models.Model):
    main = models.ForeignKey(CategoryMain, on_delete=models.CASCADE, related_name="subs")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("main", "name")

    def __str__(self) -> str:
        return f"{self.main.name} / {self.name}"


class Receipt(models.Model):
    STATUS_PROCESSING = "processing"
    STATUS_READY = "ready"
    STATUS_CONFIRMED = "confirmed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PROCESSING, "Processing"),
        (STATUS_READY, "Ready"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name="receipts"
    )
    organization = models.ForeignKey(
        "accounts.Organization", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="receipts"
    )
    payer = models.CharField(max_length=100, blank=True, default="")
    merchant = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=300, blank=True)
    purchased_at = models.DateTimeField(null=True, blank=True)
    currency = models.CharField(max_length=8, default="GBP")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROCESSING)
    image = models.ImageField(upload_to="receipts/%Y/%m/", blank=True)
    raw_model_output = models.TextField(blank=True)
    raw_model_json = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Receipt {self.id}"


class ReceiptImage(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="receipts/%Y/%m/")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return f"ReceiptImage {self.id} (receipt={self.receipt_id})"


class ReceiptItem(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="items")
    category_main = models.ForeignKey(
        CategoryMain, on_delete=models.SET_NULL, null=True, blank=True, related_name="items"
    )
    category_sub = models.ForeignKey(
        CategorySub, on_delete=models.SET_NULL, null=True, blank=True, related_name="items"
    )
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("1"))
    unit = models.CharField(max_length=50, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    line_index = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.name} ({self.receipt_id})"
