import uuid

from django.conf import settings
from django.db import models


class CreditBalance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_balance",
    )
    balance_seconds = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        minutes = self.balance_seconds // 60
        return f"{self.user} — {minutes}min ({self.balance_seconds}s)"


class CreditTransaction(models.Model):
    class TxType(models.TextChoices):
        PURCHASE = "purchase", "Purchase"
        USAGE = "usage", "Usage"
        REFUND = "refund", "Refund"
        GRANT = "grant", "Grant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_transactions",
    )
    tx_type = models.CharField(max_length=20, choices=TxType.choices)
    amount_seconds = models.IntegerField(help_text="Positive=credit, negative=debit")
    balance_after = models.PositiveIntegerField()
    description = models.CharField(max_length=500, blank=True)
    apple_transaction_id = models.CharField(
        max_length=200, blank=True, default="", db_index=True
    )
    apple_product_id = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        sign = "+" if self.amount_seconds >= 0 else ""
        return f"{self.user} {self.get_tx_type_display()} {sign}{self.amount_seconds}s"
