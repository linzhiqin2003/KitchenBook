import math
import logging

from django.db import transaction

from .models import CreditBalance, CreditTransaction

logger = logging.getLogger(__name__)


class InsufficientCreditsError(Exception):
    def __init__(self, balance: int, required: int):
        self.balance = balance
        self.required = required
        super().__init__(f"Insufficient credits: have {balance}s, need {required}s")


def get_balance(user) -> int:
    bal, _ = CreditBalance.objects.get_or_create(user=user)
    return bal.balance_seconds


def add_credits(
    user,
    amount_seconds: int,
    tx_type: str,
    description: str = "",
    apple_transaction_id: str = "",
    apple_product_id: str = "",
) -> CreditTransaction:
    with transaction.atomic():
        bal, _ = CreditBalance.objects.select_for_update().get_or_create(user=user)
        bal.balance_seconds += amount_seconds
        bal.save()

        tx = CreditTransaction.objects.create(
            user=user,
            tx_type=tx_type,
            amount_seconds=amount_seconds,
            balance_after=bal.balance_seconds,
            description=description,
            apple_transaction_id=apple_transaction_id,
            apple_product_id=apple_product_id,
        )
    logger.info(
        "Credit %s: user=%s amount=%+ds balance=%ds tx=%s",
        tx_type, user.pk, amount_seconds, bal.balance_seconds, tx.pk,
    )
    return tx


def deduct_for_audio(user, duration_seconds: float) -> CreditTransaction:
    required = math.ceil(duration_seconds)
    balance = get_balance(user)
    if balance < required:
        raise InsufficientCreditsError(balance, required)

    return add_credits(
        user,
        amount_seconds=-required,
        tx_type=CreditTransaction.TxType.USAGE,
        description=f"ASR usage: {required}s audio",
    )


def get_audio_duration(file_path: str) -> float:
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(file_path)
        if audio is not None and audio.info is not None:
            return audio.info.length
    except Exception:
        pass
    # Fallback: estimate from file size (assuming ~16kHz 16-bit mono WAV)
    import os
    size = os.path.getsize(file_path)
    return max(1.0, size / 32000)
