"""Fernet-based encryption for API keys stored in the database."""

from __future__ import annotations

import base64
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Return a cached Fernet instance using FIELD_ENCRYPTION_KEY."""
    global _fernet
    if _fernet is None:
        key = getattr(settings, "FIELD_ENCRYPTION_KEY", "")
        if not key:
            raise RuntimeError(
                "FIELD_ENCRYPTION_KEY is not set. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        # Accept both raw base64 key and plain string
        if isinstance(key, str):
            key = key.encode()
        _fernet = Fernet(key)
    return _fernet


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt a plaintext API key. Empty strings pass through."""
    if not plaintext:
        return plaintext
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """Decrypt an encrypted API key.

    Legacy fallback: if the value looks like a plaintext Groq key (starts
    with ``gsk_``), return it as-is.  This handles the migration transition
    period where some rows are not yet encrypted.
    """
    if not ciphertext:
        return ciphertext
    # Legacy plaintext key — not yet encrypted
    if ciphertext.startswith("gsk_"):
        return ciphertext
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception) as exc:
        logger.warning("Failed to decrypt API key (returning empty): %s", exc)
        return ""
