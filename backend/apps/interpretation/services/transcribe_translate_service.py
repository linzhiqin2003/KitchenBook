"""
Transcribe + Translate pipeline:
  1. Groq Whisper (whisper-large-v3) — ASR
  2. Cerebras Qwen3-32B — translation
"""

import json
import logging
import os
import re
import urllib.request
import urllib.error

from django.conf import settings as django_settings

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)

# ── Cerebras key pool (mirrors api/tools.py) ──
_cerebras_key_index = 0


def _get_cerebras_key():
    global _cerebras_key_index
    pool_str = getattr(django_settings, 'CEREBRAS_API_KEY_POOL', '')
    if not pool_str:
        return None
    keys = [k.strip() for k in pool_str.split(',') if k.strip()]
    if not keys:
        return None
    key = keys[_cerebras_key_index % len(keys)]
    _cerebras_key_index += 1
    return key


def _cerebras_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Call Cerebras Qwen3-32B for translation."""
    key = _get_cerebras_key()
    if not key:
        raise RuntimeError("CEREBRAS_API_KEY_POOL not configured")

    system_msg = (
        f"/no_think\nYou are a professional translator. "
        f"Translate the following {source_lang} text into {target_lang}. "
        f"Output ONLY the translation, nothing else."
    )
    payload = json.dumps({
        "model": "qwen-3-32b",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": text},
        ],
        "max_tokens": 4096,
        "temperature": 0.1,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.cerebras.ai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    result = (data["choices"][0]["message"].get("content") or "").strip()
    # Strip <think>...</think> tags from Qwen3 reasoning model
    result = re.sub(r'<think>[\s\S]*?</think>\s*', '', result).strip()
    return result


def _groq_transcribe(file_path: str) -> str:
    """Transcribe audio using Groq Whisper. Returns transcribed text."""
    if not Groq:
        raise ImportError("groq package not installed")

    from common.config import get_settings
    api_settings = get_settings()
    groq_key = api_settings.api.groq_api_key or os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        raise RuntimeError("GROQ_API_KEY not configured")

    client = Groq(api_key=groq_key)
    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(file_path), f.read()),
            model="whisper-large-v3",
            response_format="json",
            temperature=0.0,
        )
    text = transcription.text.strip()
    logger.info("Groq transcription done (%d chars)", len(text))
    return text


def transcribe_and_translate(file_path: str, source_lang: str, target_lang: str):
    """
    Full pipeline: Groq Whisper transcription → Cerebras translation.

    Returns dict: { transcription, translation, source_lang, target_lang }
    Raises on failure.
    """
    text = _groq_transcribe(file_path)

    if not text:
        return {
            "transcription": "",
            "translation": "",
            "source_lang": source_lang,
            "target_lang": target_lang,
        }

    translated = _cerebras_translate(text, source_lang, target_lang)
    logger.info("Cerebras translation done (%d chars)", len(translated))

    return {
        "transcription": text,
        "translation": translated,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }


def transcribe_and_translate_stream(file_path: str, source_lang: str, target_lang: str):
    """
    Streaming pipeline: yield NDJSON lines — transcription first, then translation.
    Each line is a JSON object with an 'event' field.
    """
    # Step 1: Groq Whisper transcription
    text = _groq_transcribe(file_path)
    yield json.dumps({"event": "transcription", "text": text}) + "\n"

    if not text:
        yield json.dumps({"event": "done"}) + "\n"
        return

    # Step 2: Cerebras translation
    translated = _cerebras_translate(text, source_lang, target_lang)
    logger.info("Cerebras translation done (%d chars)", len(translated))
    yield json.dumps({"event": "translation", "text": translated}) + "\n"
    yield json.dumps({"event": "done"}) + "\n"
