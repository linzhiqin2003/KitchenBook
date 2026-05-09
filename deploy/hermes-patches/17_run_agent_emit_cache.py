"""Make _run_agent emit cache_read/cache_write so patch12's SSE chunk has
real cache data instead of zero.

Bug
---
``api_server.py::_run_agent`` constructs a usage dict from the agent's
``session_*`` counters but only picks four fields::

    usage = {
        "input_tokens":  getattr(agent, "session_prompt_tokens", 0) or 0,  # ←含 cache
        "output_tokens": getattr(agent, "session_completion_tokens", 0) or 0,
        "total_tokens":  getattr(agent, "session_total_tokens", 0) or 0,
        "last_prompt_tokens": ...,
    }

Two problems:

1. ``input_tokens`` is set to ``session_prompt_tokens``.  In Hermes' agent
   bookkeeping (run_agent.py:11050-11057) ``session_prompt_tokens``
   accumulates the upstream OpenAI ``prompt_tokens`` field, **which
   already includes cache hits**.  Meanwhile ``session_input_tokens``
   accumulates ``canonical_usage.input_tokens`` — the non-cache portion.
   The field name "input_tokens" should mean non-cache input.

2. ``cache_read_tokens`` and ``cache_write_tokens`` are missing entirely.
   Hermes tracks them via ``session_cache_read_tokens`` /
   ``session_cache_write_tokens`` (filled at run_agent.py:11056-11057),
   and even includes them in ``run_conversation``'s result dict
   (run_agent.py:13136-13137), but ``_run_agent`` discards them.

Patch12 then computes the SSE chunk's ``prompt_tokens`` as::

    input_tokens + cache_read_tokens + cache_write_tokens

With the bug, that's ``session_prompt_tokens + 0 + 0`` — the right total
by accident, but ``cache_tokens`` (= cache_read + cache_write) is always
zero, so the web client cannot split cache vs. non-cache for cost.

Fix
---
Switch ``input_tokens`` to ``session_input_tokens`` (non-cache) and add
``cache_read_tokens`` / ``cache_write_tokens``.  Patch12's reconstruction
``input + cache_read + cache_write`` still equals the OpenAI
``prompt_tokens`` total, but now ``cache_tokens`` carries real upstream
data.

The web client doesn't read ``input_tokens`` directly (only the derived
``prompt_tokens``, ``cache_tokens``, ``completion_tokens``,
``last_prompt_tokens``), so the field-name semantic change is safe.

Idempotent — keyed off SENTINEL appearing in the file.
"""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "# [patch17] cache passthrough in _run_agent"

OLD = (
    '            usage = {\n'
    '                "input_tokens": getattr(agent, "session_prompt_tokens", 0) or 0,\n'
    '                "output_tokens": getattr(agent, "session_completion_tokens", 0) or 0,\n'
    '                "total_tokens": getattr(agent, "session_total_tokens", 0) or 0,\n'
    '                # The actual prompt size of the LAST API call — what the\n'
    '                # model just saw — separated from the per-call sum above\n'
    '                # so the UI can render a meaningful Context Window value.\n'
    '                "last_prompt_tokens": getattr(\n'
    '                    getattr(agent, "context_compressor", None), "last_prompt_tokens", 0\n'
    '                ) or 0,\n'
    '            }\n'
)

NEW = (
    '            usage = {\n'
    '                # [patch17] cache passthrough in _run_agent — input_tokens\n'
    '                # is the non-cache portion (was session_prompt_tokens which\n'
    '                # already counts cache); add cache_read/write so patch12\'s\n'
    '                # downstream reconstruction stays correct AND carries real\n'
    '                # cache data to the client cost split.\n'
    '                "input_tokens": getattr(agent, "session_input_tokens", 0) or 0,\n'
    '                "output_tokens": getattr(agent, "session_completion_tokens", 0) or 0,\n'
    '                "total_tokens": getattr(agent, "session_total_tokens", 0) or 0,\n'
    '                "cache_read_tokens": getattr(agent, "session_cache_read_tokens", 0) or 0,\n'
    '                "cache_write_tokens": getattr(agent, "session_cache_write_tokens", 0) or 0,\n'
    '                # The actual prompt size of the LAST API call — what the\n'
    '                # model just saw — separated from the per-call sum above\n'
    '                # so the UI can render a meaningful Context Window value.\n'
    '                "last_prompt_tokens": getattr(\n'
    '                    getattr(agent, "context_compressor", None), "last_prompt_tokens", 0\n'
    '                ) or 0,\n'
    '            }\n'
)


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("  [skip] already patched")
        return 0
    if OLD not in text:
        print("FATAL: anchor not found", file=sys.stderr)
        return 2
    bak = P.with_suffix(P.suffix + ".cachepass.bak")
    if not bak.exists():
        shutil.copy2(P, bak)
        print(f"  backup -> {bak.name}")
    P.write_text(text.replace(OLD, NEW))
    import ast
    try:
        ast.parse(P.read_text(), str(P))
        print("  AST ok")
    except SyntaxError as e:
        print(f"AST FAIL: {e}", file=sys.stderr)
        shutil.copy2(bak, P)
        return 3
    print("  patched _run_agent usage dict")
    return 0


if __name__ == "__main__":
    sys.exit(main())
