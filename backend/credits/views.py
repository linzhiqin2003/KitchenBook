import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services import get_balance
from .models import CreditTransaction
from .serializers import (
    CreditBalanceSerializer,
    CreditTransactionSerializer,
    VerifyPurchaseSerializer,
)
from .apple_iap import fulfill_purchase

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def balance_view(request):
    balance = get_balance(request.user)
    return Response({"balance_seconds": balance})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def history_view(request):
    txs = CreditTransaction.objects.filter(user=request.user).order_by("-created_at")[:50]
    serializer = CreditTransactionSerializer(txs, many=True)
    return Response({"transactions": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_purchase_view(request):
    serializer = VerifyPurchaseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    jws_transaction = serializer.validated_data["jws_transaction"]

    try:
        result = fulfill_purchase(request.user, jws_transaction)
        return Response(result)
    except ValueError as e:
        logger.warning("IAP verification failed: %s", e)
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error("IAP verification error: %s", e, exc_info=True)
        return Response(
            {"error": "Purchase verification failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
