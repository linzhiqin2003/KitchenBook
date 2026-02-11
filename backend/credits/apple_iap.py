"""Apple In-App Purchase JWS verification and credit fulfillment."""

import base64
import logging

import jwt
from cryptography.x509 import load_der_x509_certificate

from .models import CreditTransaction
from .services import add_credits

logger = logging.getLogger(__name__)

# Product ID → seconds mapping
PRODUCT_CREDITS = {
    "org.lzqqq.interpretation.credits.60": 3600,     # 60 min
    "org.lzqqq.interpretation.credits.300": 18000,    # 300 min
    "org.lzqqq.interpretation.credits.600": 36000,    # 600 min
}


def _get_public_key_from_x5c(x5c_chain: list):
    """Extract the public key from the leaf certificate in the x5c chain."""
    leaf_cert_der = base64.b64decode(x5c_chain[0])
    cert = load_der_x509_certificate(leaf_cert_der)
    return cert.public_key()


def verify_jws_transaction(jws_transaction: str) -> dict:
    """Verify an Apple JWS transaction and return the decoded payload.

    For Xcode StoreKit testing (environment="Xcode"), signature verification
    is skipped since Xcode uses local signing keys.

    For Production/Sandbox, the signature is verified using the x5c
    certificate chain embedded in the JWS header.
    """
    # Peek at the payload without verification to check environment
    unverified_payload = jwt.decode(
        jws_transaction,
        options={"verify_signature": False},
        algorithms=["ES256"],
    )
    environment = unverified_payload.get("environment", "")

    if environment == "Xcode":
        logger.info("Xcode StoreKit testing: skipped JWS signature verification")
        return unverified_payload

    # For Production/Sandbox, verify signature using x5c certificate chain
    header = jwt.get_unverified_header(jws_transaction)
    x5c = header.get("x5c", [])

    if not x5c:
        raise ValueError("JWS header missing x5c certificate chain")

    public_key = _get_public_key_from_x5c(x5c)
    payload = jwt.decode(
        jws_transaction,
        key=public_key,
        algorithms=["ES256"],
        options={"verify_aud": False},
    )
    logger.info("Apple JWS verified (environment=%s)", environment)
    return payload


def fulfill_purchase(user, jws_transaction: str) -> dict:
    """Verify Apple JWS transaction and add credits to user.

    Returns dict with status and details.
    """
    payload = verify_jws_transaction(jws_transaction)

    transaction_id = str(payload.get("transactionId", ""))
    product_id = payload.get("productId", "")

    # Check for duplicate
    if transaction_id and CreditTransaction.objects.filter(
        apple_transaction_id=transaction_id
    ).exists():
        logger.warning("Duplicate Apple transaction: %s", transaction_id)
        return {
            "status": "duplicate",
            "message": "Transaction already processed",
            "transaction_id": transaction_id,
        }

    # Lookup product credits
    credit_seconds = PRODUCT_CREDITS.get(product_id)
    if credit_seconds is None:
        raise ValueError(f"Unknown product ID: {product_id}")

    # Add credits
    tx = add_credits(
        user=user,
        amount_seconds=credit_seconds,
        tx_type=CreditTransaction.TxType.PURCHASE,
        description=f"Apple IAP: {product_id}",
        apple_transaction_id=transaction_id,
        apple_product_id=product_id,
    )

    from .services import get_balance
    balance = get_balance(user)

    logger.info(
        "Apple IAP fulfilled: user=%s product=%s credits=%ds tx=%s",
        user.pk, product_id, credit_seconds, tx.pk,
    )

    return {
        "status": "success",
        "transaction_id": transaction_id,
        "product_id": product_id,
        "credits_added": credit_seconds,
        "balance_seconds": balance,
    }
