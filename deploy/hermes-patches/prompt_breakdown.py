"""Per-section token breakdown for the request payload.

Splits the prompt into the buckets that actually fill the context window
(identity, tool guidance, memory, skills, context files, env meta, user
system, tools, messages, ephemeral system) so the UI can show a Claude
Code-style composition view instead of a single opaque ``prompt_tokens``.

Tokenization uses ``tiktoken`` with the ``o200k_base`` encoding when
available — the most universal modern BPE, close enough across
OpenAI/Anthropic/Gemini for a UI breakdown.  Falls back to
``cl100k_base`` and finally to char/4 if neither encoding can be loaded.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Per-message structural overhead (role wrapper, separators) — matches the
# convention used by OpenAI's tokenization cookbook (`tokens_per_message=3`).
_PER_MESSAGE_OVERHEAD = 3

_ENCODER = None
_ENCODER_NAME: Optional[str] = None
_ENCODER_LOADED = False


def _load_encoder():
    """Lazy-load the BPE encoder; cache failures so we don't retry."""
    global _ENCODER, _ENCODER_NAME, _ENCODER_LOADED
    if _ENCODER_LOADED:
        return _ENCODER
    _ENCODER_LOADED = True
    try:
        import tiktoken  # type: ignore

        for name in ("o200k_base", "cl100k_base"):
            try:
                _ENCODER = tiktoken.get_encoding(name)
                _ENCODER_NAME = name
                logger.debug("prompt_breakdown: using tiktoken encoding %s", name)
                return _ENCODER
            except Exception as exc:
                logger.debug("prompt_breakdown: encoding %s unavailable (%s)", name, exc)
        _ENCODER = None
    except ImportError:
        logger.debug("prompt_breakdown: tiktoken not installed; using char/4 fallback")
        _ENCODER = None
    return _ENCODER


def encoder_name() -> str:
    """Return the active encoding name, or ``"char/4"`` for the fallback."""
    _load_encoder()
    return _ENCODER_NAME or "char/4"


def count_text(text: str) -> int:
    """Count tokens in *text* using the cached BPE encoder."""
    if not text:
        return 0
    enc = _load_encoder()
    if enc is None:
        return (len(text) + 3) // 4
    try:
        return len(enc.encode(text, disallowed_special=()))
    except Exception:
        return (len(text) + 3) // 4


def count_messages(messages: Optional[List[Dict[str, Any]]]) -> int:
    """Count tokens for an OpenAI-style ``messages`` list.

    Serializes each message with ``json.dumps`` so role, content, name,
    tool_calls and tool_call_id all contribute, then adds a constant
    per-message overhead (matches the OpenAI cookbook formula).
    """
    if not messages:
        return 0
    total = 0
    for msg in messages:
        try:
            payload = json.dumps(msg, ensure_ascii=False, default=str)
        except Exception:
            payload = str(msg)
        total += count_text(payload)
    total += _PER_MESSAGE_OVERHEAD * len(messages)
    return total


def count_tools(tools: Optional[List[Dict[str, Any]]]) -> int:
    """Count tokens for a tool-definitions list (OpenAI tool schema)."""
    if not tools:
        return 0
    try:
        return count_text(json.dumps(tools, ensure_ascii=False, default=str))
    except Exception:
        return sum(count_text(str(t)) for t in tools)


def count_segments(segments: Optional[Dict[str, str]]) -> Dict[str, int]:
    """Run ``count_text`` over each (label → text) entry."""
    if not segments:
        return {}
    return {label: count_text(text or "") for label, text in segments.items()}


# ── Public schema ──────────────────────────────────────────────────────
# Order matters — UI renders rows in this order.

BREAKDOWN_LABELS: Dict[str, str] = {
    "identity": "Agent identity",
    "tool_guidance": "Tool guidance",
    "user_system": "User system prompt",
    "memory_files": "Memory files",
    "skills": "Skills",
    "context_files": "Context files",
    "env_meta": "Env / time / platform",
    "ephemeral_system": "Ephemeral system",
    "tools": "Tool definitions",
    "messages": "Messages",
}


def make_breakdown(
    segments: Dict[str, str],
    *,
    tools: Optional[List[Dict[str, Any]]] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    ephemeral_system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the breakdown dict that's exposed via the API.

    Returns ``{"sections": {key: {label, tokens}}, "total_local": int,
    "encoding": str}``.  ``total_local`` is the local-tokenizer sum and
    will not exactly match the provider's reported ``prompt_tokens`` —
    callers should treat it as a composition-view aid, not ground truth.
    """
    sec_text = dict(segments or {})
    if ephemeral_system_prompt:
        sec_text["ephemeral_system"] = ephemeral_system_prompt
    counts = count_segments(sec_text)
    counts["tools"] = count_tools(tools)
    counts["messages"] = count_messages(messages)

    # Emit in a stable, UI-friendly order.  Drop zero rows so the panel
    # only shows what's actually contributing.
    sections: Dict[str, Dict[str, Any]] = {}
    for key, label in BREAKDOWN_LABELS.items():
        tokens = int(counts.get(key, 0) or 0)
        if tokens <= 0:
            continue
        sections[key] = {"label": label, "tokens": tokens}

    return {
        "sections": sections,
        "total_local": sum(int(v) for v in counts.values()),
        "encoding": encoder_name(),
    }
