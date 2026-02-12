"""Groq API key pool with per-key cooldown and round-robin rotation.

All user keys (decrypted via EncryptedCharField) + server env key are
pooled together.  When a key gets 429'd, it enters a 60-second cooldown
persisted as a temp file so all gunicorn workers see it.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
import tempfile
import threading
import time
import wave

from django.conf import settings as django_settings

logger = logging.getLogger(__name__)

# ── Pool config ──
_POOL_CACHE_TTL = 300  # seconds between DB refreshes
_KEY_COOLDOWN_SECS = 60
_COOLDOWN_DIR = os.path.join(tempfile.gettempdir(), "groq_cooldown", "keys")

# ── Thread-safe cache ──
_lock = threading.Lock()
_pool_cache: list[str] = []
_pool_cache_time: float = 0


def _load_all_keys() -> list[str]:
    """Load all unique Groq keys from DB + server env."""
    keys: set[str] = set()

    server_key = getattr(django_settings, "GROQ_API_KEY", "")
    if server_key:
        keys.add(server_key)

    try:
        from accounts.models import UserProfile
        for key in (
            UserProfile.objects
            .exclude(groq_api_key="")
            .values_list("groq_api_key", flat=True)
        ):
            # EncryptedCharField.from_db_value already decrypts
            if key:
                keys.add(key)
    except Exception as exc:
        logger.warning("Failed to load user Groq keys: %s", exc)

    return list(keys)


def _refresh_pool() -> list[str]:
    """Double-check locking refresh."""
    global _pool_cache, _pool_cache_time
    now = time.time()
    if now - _pool_cache_time < _POOL_CACHE_TTL:
        return _pool_cache
    with _lock:
        # Re-check after acquiring lock
        if now - _pool_cache_time < _POOL_CACHE_TTL:
            return _pool_cache
        _pool_cache = _load_all_keys()
        _pool_cache_time = now
        logger.info("Groq key pool refreshed: %d keys", len(_pool_cache))
        return _pool_cache


def _key_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def _cooldown_path(key: str) -> str:
    return os.path.join(_COOLDOWN_DIR, _key_hash(key))


def _is_cooled_down(key: str) -> bool:
    """Return True if this key is in cooldown (should be skipped)."""
    try:
        path = _cooldown_path(key)
        if not os.path.exists(path):
            return False
        expiry = float(open(path).read().strip())
        return time.time() < expiry
    except (ValueError, OSError):
        return False


def mark_key_rate_limited(key: str) -> None:
    """Record a cooldown timestamp for a rate-limited key."""
    try:
        os.makedirs(_COOLDOWN_DIR, exist_ok=True)
        with open(_cooldown_path(key), "w") as f:
            f.write(str(time.time() + _KEY_COOLDOWN_SECS))
        logger.info("Groq key %s…%s marked rate-limited for %ds",
                     key[:8], key[-4:], _KEY_COOLDOWN_SECS)
    except OSError:
        pass


def get_available_keys(preferred_key: str | None = None) -> list[str]:
    """Return ordered list of available (non-cooled-down) keys.

    ``preferred_key`` (the user's own key) is placed first if available.
    """
    all_keys = _refresh_pool()
    available = [k for k in all_keys if not _is_cooled_down(k)]

    if preferred_key:
        # Ensure preferred key is first, even if not in pool (user just set it)
        if preferred_key in available:
            available.remove(preferred_key)
        elif not _is_cooled_down(preferred_key):
            pass  # will be prepended below
        else:
            # preferred key is cooled down; don't prepend
            preferred_key = None

    if preferred_key:
        available.insert(0, preferred_key)

    # If everything is cooled down, return the preferred key anyway as a
    # last-ditch attempt (cooldown is approximate).
    if not available and preferred_key:
        available = [preferred_key]

    return available


# ── Probe: send silent WAV to Whisper to detect rate limiting ──

def _make_silent_wav() -> bytes:
    """Generate a minimal 0.5s 16kHz mono silent WAV in memory."""
    sample_rate = 16000
    n_samples = sample_rate // 2  # 0.5 seconds
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_samples)
    return buf.getvalue()


_PROBE_WAV = _make_silent_wav()


def probe_key(api_key: str) -> bool:
    """Send a silent WAV to Groq Whisper to check if the key is usable.

    - 200 (success) → True (key works)
    - 400 (bad request / audio too short) → True (key works, audio was just bad)
    - 429 (rate limited) → False
    - 401 (auth error) → False
    """
    try:
        from groq import (
            Groq,
            RateLimitError,
            AuthenticationError,
            BadRequestError,
        )
    except ImportError:
        return False

    try:
        client = Groq(api_key=api_key)
        client.audio.transcriptions.create(
            file=("probe.wav", _PROBE_WAV),
            model="whisper-large-v3-turbo",
            response_format="json",
            temperature=0.0,
        )
        return True
    except RateLimitError:
        return False
    except AuthenticationError:
        return False
    except BadRequestError:
        return True  # key works, audio was just too short
    except Exception:
        return False


def find_working_key(exclude_key: str | None = None, max_probes: int = 5) -> str | None:
    """Probe pool keys with a silent WAV and return the first usable one.

    Skips cooled-down keys, probes up to ``max_probes`` candidates.
    """
    all_keys = _refresh_pool()
    candidates = [k for k in all_keys if k != exclude_key and not _is_cooled_down(k)]

    for key in candidates[:max_probes]:
        if probe_key(key):
            logger.info("Probe found working key %s…%s", key[:8], key[-4:])
            return key
        else:
            mark_key_rate_limited(key)

    return None
