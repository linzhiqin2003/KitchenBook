"""
Transcribe + Translate pipeline:
  1. Qwen3-ASR-1.7B (primary) / Groq Whisper (fallback) — ASR
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

# ── Source language code mapping for Qwen3-ASR ──
# Qwen3-ASR supports: zh, en, yue, ar, de, fr, es, pt, id, it, ko, ru, th, vi, ja, tr, hi, ms, nl, sv, da, fi, pl, cs, fil, fa, el, hu, mk, ro
_QWEN3_ASR_LANGS = {
    'zh', 'en', 'yue', 'ar', 'de', 'fr', 'es', 'pt', 'id', 'it', 'ko',
    'ru', 'th', 'vi', 'ja', 'tr', 'hi', 'ms', 'nl', 'sv', 'da', 'fi',
    'pl', 'cs', 'fil', 'fa', 'el', 'hu', 'mk', 'ro',
}

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


def _qwen3_asr_transcribe(file_path: str, source_lang: str = "") -> str:
    """Transcribe audio using self-hosted Qwen3-ASR-1.7B. Returns transcribed text."""
    base_url = getattr(django_settings, 'QWEN3_ASR_BASE_URL', '')
    if not base_url:
        raise RuntimeError("QWEN3_ASR_BASE_URL not configured")

    url = f"{base_url.rstrip('/')}/v1/audio/transcriptions"

    # Build multipart/form-data manually using urllib (no requests dependency)
    import mimetypes
    boundary = f"----WebKitFormBoundary{os.urandom(8).hex()}"

    with open(file_path, "rb") as f:
        file_data = f.read()

    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(filename)[0] or "audio/wav"

    parts = []
    # file field
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    )
    parts.append(file_data)
    parts.append(b"\r\n")
    # model field
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"Qwen/Qwen3-ASR-1.7B\r\n"
    )
    # response_format field
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="response_format"\r\n\r\n'
        f"json\r\n"
    )
    # language field (optional)
    lang_code = source_lang.lower() if source_lang else ""
    if lang_code and lang_code in _QWEN3_ASR_LANGS:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="language"\r\n\r\n'
            f"{lang_code}\r\n"
        )
    parts.append(f"--{boundary}--\r\n")

    # Encode body
    body = b""
    for part in parts:
        if isinstance(part, str):
            body += part.encode("utf-8")
        else:
            body += part

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": "Bearer EMPTY",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    text = (data.get("text") or "").strip()
    logger.info("Qwen3-ASR transcription done (%d chars)", len(text))
    return text


def _groq_transcribe(file_path: str) -> str:
    """Transcribe audio using Groq Whisper (fallback). Returns transcribed text."""
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


def _transcribe(file_path: str, source_lang: str = "") -> str:
    """Transcribe audio: try Qwen3-ASR first, fall back to Groq Whisper."""
    # Try Qwen3-ASR (self-hosted, primary)
    try:
        return _qwen3_asr_transcribe(file_path, source_lang)
    except Exception as e:
        logger.warning("Qwen3-ASR failed, falling back to Groq Whisper: %s", e)

    # Fallback to Groq Whisper
    return _groq_transcribe(file_path)


def transcribe_and_translate(file_path: str, source_lang: str, target_lang: str):
    """
    Full pipeline: Groq Whisper transcription → Cerebras translation.

    Returns dict: { transcription, translation, source_lang, target_lang }
    Raises on failure.
    """
    text = _transcribe(file_path, source_lang)

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
    text = _transcribe(file_path, source_lang)
    yield json.dumps({"event": "transcription", "text": text}) + "\n"

    if not text:
        yield json.dumps({"event": "done"}) + "\n"
        return

    # Step 2: Cerebras translation
    translated = _cerebras_translate(text, source_lang, target_lang)
    logger.info("Cerebras translation done (%d chars)", len(translated))
    yield json.dumps({"event": "translation", "text": translated}) + "\n"
    yield json.dumps({"event": "done"}) + "\n"


def _cerebras_summarize_stream(text: str):
    """Call Cerebras Qwen3-32B to generate meeting minutes, streaming."""
    key = _get_cerebras_key()
    if not key:
        raise RuntimeError("CEREBRAS_API_KEY_POOL not configured")

    system_msg = (
        "/no_think\n"
        "你是一位专业的会议记录员。根据以下会议转录内容，生成结构化的中文会议纪要。\n"
        "格式要求：\n"
        "## 会议主题\n"
        "（一句话概括会议主题）\n\n"
        "## 要点摘要\n"
        "- 要点1\n"
        "- 要点2\n\n"
        "## 行动项\n"
        "- [ ] 行动项1\n"
        "- [ ] 行动项2\n\n"
        "## 结论\n"
        "（总结会议结论）\n\n"
        "如果内容不像会议（例如是演讲、访谈等），请相应调整标题和格式。"
    )
    payload = json.dumps({
        "model": "qwen-3-32b",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": text},
        ],
        "max_tokens": 4096,
        "temperature": 0.3,
        "stream": True,
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
    resp = urllib.request.urlopen(req, timeout=60)
    try:
        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            chunk = json.loads(data_str)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content", "")
            if content:
                # Strip <think>...</think> fragments
                content = re.sub(r'<think>[\s\S]*?</think>\s*', '', content)
                if content:
                    yield content
    finally:
        resp.close()


def generate_minutes_stream(entries):
    """
    Generate meeting minutes from transcription entries.
    Yields NDJSON lines: {"event": "chunk", "text": "..."} then {"event": "done"}.
    entries: list of {"original": str, "translated": str}
    """
    # Build combined text from all entries
    parts = []
    for i, entry in enumerate(entries, 1):
        original = entry.get("original", "")
        translated = entry.get("translated", "")
        if original and translated:
            parts.append(f"[{i}] {original}\n    翻译: {translated}")
        elif original:
            parts.append(f"[{i}] {original}")
    combined = "\n\n".join(parts)

    if not combined.strip():
        yield json.dumps({"event": "error", "text": "没有有效的转录内容"}) + "\n"
        return

    try:
        for chunk in _cerebras_summarize_stream(combined):
            yield json.dumps({"event": "chunk", "text": chunk}) + "\n"
        yield json.dumps({"event": "done"}) + "\n"
    except Exception as e:
        logger.error("generate_minutes_stream error: %s", e, exc_info=True)
        yield json.dumps({"event": "error", "text": str(e)}) + "\n"
