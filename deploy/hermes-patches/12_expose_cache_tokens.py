"""Pass cache_tokens through to the OpenAI-compatible chat-completion
response so the web client can split cache vs. non-cache input for
cost estimation.

Hermes' agent already tracks ``session_cache_read_tokens`` /
``session_cache_write_tokens`` (run_agent.py around line 10990) and
returns them in the usage dict (line 13072).  The api_server platform
shapes that into the OpenAI ``usage`` object but only emits
``prompt_tokens / completion_tokens / total_tokens`` (+ our
last_prompt_tokens / breakdown patches), dropping cache info.

Patch both emission sites — the non-stream JSON response (~1644) and
the SSE finish chunk (~1766) — to also include::

    "cache_tokens":  cache_read + cache_write           # for billing
    "cache_read_tokens":  cache_read                    # raw read
    "cache_write_tokens": cache_write                   # raw write

The web side bills ``cache_tokens`` at the cache-hit rate and treats
``prompt_tokens - cache_tokens`` as billable input.

Idempotent — keyed off SENTINEL appearing in the file."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "# [patch12] cache token passthrough"

OLD = (
    '            "usage": {\n'
    '                "prompt_tokens": usage.get("input_tokens", 0),\n'
    '                "completion_tokens": usage.get("output_tokens", 0),\n'
    '                "total_tokens": usage.get("total_tokens", 0),\n'
    '                **({"breakdown": usage["breakdown"]} if usage.get("breakdown") else {}),\n'
    '                **({"last_prompt_tokens": usage["last_prompt_tokens"]} if usage.get("last_prompt_tokens") else {}),\n'
    '            },\n'
)

NEW = (
    '            "usage": {\n'
    '                # [patch12] cache token passthrough — read + write merged into\n'
    '                # cache_tokens for unified cache-rate billing on the client.\n'
    '                "prompt_tokens": (usage.get("input_tokens", 0) or 0) + (usage.get("cache_read_tokens", 0) or 0) + (usage.get("cache_write_tokens", 0) or 0),\n'
    '                "completion_tokens": usage.get("output_tokens", 0),\n'
    '                "total_tokens": usage.get("total_tokens", 0),\n'
    '                "cache_tokens": (usage.get("cache_read_tokens", 0) or 0) + (usage.get("cache_write_tokens", 0) or 0),\n'
    '                "cache_read_tokens": usage.get("cache_read_tokens", 0) or 0,\n'
    '                "cache_write_tokens": usage.get("cache_write_tokens", 0) or 0,\n'
    '                **({"breakdown": usage["breakdown"]} if usage.get("breakdown") else {}),\n'
    '                **({"last_prompt_tokens": usage["last_prompt_tokens"]} if usage.get("last_prompt_tokens") else {}),\n'
    '            },\n'
)

OLD_SSE = (
    '                "usage": {\n'
    '                    "prompt_tokens": usage.get("input_tokens", 0),\n'
    '                    "completion_tokens": usage.get("output_tokens", 0),\n'
    '                    "total_tokens": usage.get("total_tokens", 0),\n'
    '                    **({"breakdown": usage["breakdown"]} if usage.get("breakdown") else {}),\n'
    '                **({"last_prompt_tokens": usage["last_prompt_tokens"]} if usage.get("last_prompt_tokens") else {}),\n'
    '                },\n'
)

NEW_SSE = (
    '                "usage": {\n'
    '                    # [patch12] cache token passthrough — see non-stream branch.\n'
    '                    "prompt_tokens": (usage.get("input_tokens", 0) or 0) + (usage.get("cache_read_tokens", 0) or 0) + (usage.get("cache_write_tokens", 0) or 0),\n'
    '                    "completion_tokens": usage.get("output_tokens", 0),\n'
    '                    "total_tokens": usage.get("total_tokens", 0),\n'
    '                    "cache_tokens": (usage.get("cache_read_tokens", 0) or 0) + (usage.get("cache_write_tokens", 0) or 0),\n'
    '                    "cache_read_tokens": usage.get("cache_read_tokens", 0) or 0,\n'
    '                    "cache_write_tokens": usage.get("cache_write_tokens", 0) or 0,\n'
    '                    **({"breakdown": usage["breakdown"]} if usage.get("breakdown") else {}),\n'
    '                **({"last_prompt_tokens": usage["last_prompt_tokens"]} if usage.get("last_prompt_tokens") else {}),\n'
    '                },\n'
)


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("  [skip] already patched")
        return 0
    if OLD not in text or OLD_SSE not in text:
        print("FATAL: anchor not found", file=sys.stderr)
        if OLD not in text:
            print("  missed: non-stream usage block", file=sys.stderr)
        if OLD_SSE not in text:
            print("  missed: SSE finish-chunk usage block", file=sys.stderr)
        return 2
    bak = P.with_suffix(P.suffix + ".cachetok.bak")
    if not bak.exists():
        shutil.copy2(P, bak)
        print(f"  backup -> {bak.name}")
    new_text = text.replace(OLD, NEW).replace(OLD_SSE, NEW_SSE)
    P.write_text(new_text)
    import ast
    try:
        ast.parse(P.read_text(), str(P))
        print("  AST ok")
    except SyntaxError as e:
        print(f"AST FAIL: {e}", file=sys.stderr)
        shutil.copy2(bak, P)
        return 3
    print("  patched (non-stream + SSE)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
