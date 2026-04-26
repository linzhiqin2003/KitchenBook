"""DeepSeek model constants and client helpers.

Centralizes model selection so future migrations only touch this file.

Background
----------
DeepSeek deprecated `deepseek-chat` and `deepseek-reasoner` (sunset 2026/07/24).
Both map to the new `deepseek-v4-flash` family:
- `deepseek-chat` ≈ `deepseek-v4-flash` non-thinking
- `deepseek-reasoner` ≈ `deepseek-v4-flash` thinking-enabled
- `deepseek-v4-pro` is the higher-quality option (not used here per project policy)
"""
from __future__ import annotations

from typing import Any, Dict, Optional

# Single canonical model — all calls use this and toggle thinking via extra_body.
CHAT_MODEL = "deepseek-v4-flash"
REASONER_MODEL = "deepseek-v4-flash"

# OpenAI-compatible base URL for DeepSeek.
BASE_URL = "https://api.deepseek.com/v1"


def thinking_kwargs(effort: str = "high") -> Dict[str, Any]:
    """Return kwargs that enable DeepSeek's thinking mode.

    Spread into `chat.completions.create(...)` like:
        client.chat.completions.create(model=REASONER_MODEL, ..., **thinking_kwargs())

    `effort` is one of "low" | "medium" | "high".
    """
    return {
        "extra_body": {
            "thinking": {"type": "enabled"},
            "reasoning_effort": effort,
        }
    }


def non_thinking_kwargs() -> Dict[str, Any]:
    """Return kwargs that explicitly DISABLE thinking mode.

    `deepseek-v4-flash` enables thinking by default, which adds latency and
    consumes reasoning tokens. Use this for simple/fast chat calls where the
    legacy `deepseek-chat` non-thinking behavior is desired.
    """
    return {
        "extra_body": {
            "thinking": {"type": "disabled"},
        }
    }


def get_client(api_key: Optional[str] = None):
    """Return an OpenAI-compatible client for DeepSeek, or None if no key."""
    if not api_key:
        return None
    from openai import OpenAI

    return OpenAI(api_key=api_key, base_url=BASE_URL)
