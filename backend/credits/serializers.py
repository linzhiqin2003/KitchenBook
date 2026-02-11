from rest_framework import serializers
from .models import CreditBalance, CreditTransaction


class CreditBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditBalance
        fields = ["balance_seconds", "updated_at"]


class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = [
            "id", "tx_type", "amount_seconds", "balance_after",
            "description", "apple_product_id", "created_at",
        ]


class VerifyPurchaseSerializer(serializers.Serializer):
    jws_transaction = serializers.CharField()
