"""Expose ``context_compressor.last_prompt_tokens`` in the usage payload.

OpenAI-style ``prompt_tokens`` from Hermes today is the sum of EVERY
internal LLM call's prompt for one user turn — when the agent uses
tools it can be 2-4× the actual context size, and the number jumps
non-monotonically as different turns make different numbers of
internal calls.

For a "Context Window" UI, we want the size of the LAST request sent
to the model — that grows steadily with chat history and matches what
the model actually saw. Hermes already tracks this on
``agent.context_compressor.last_prompt_tokens``; surface it as a new
``last_prompt_tokens`` key on usage so the frontend can use it for the
header without losing the billing-truthy ``prompt_tokens``.

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "last_prompt_tokens"


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("[skip] already patched")
        return 0

    # Both occurrences live in the same file: one in _run_agent's executor
    # closure, one in the /v1/runs streaming path.  Patch both.
    old = (
        '                "input_tokens": getattr(agent, "session_prompt_tokens", 0) or 0,\n'
        '                "output_tokens": getattr(agent, "session_completion_tokens", 0) or 0,\n'
        '                "total_tokens": getattr(agent, "session_total_tokens", 0) or 0,\n'
        '            }\n'
    )
    new = (
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

    n = text.count(old)
    if n == 0:
        print("FATAL: usage assembly anchor not found", file=sys.stderr)
        return 2
    text = text.replace(old, new)
    print(f"  scoped {n} usage block(s)")

    bak = P.with_suffix(P.suffix + ".lpt.bak")
    if not bak.exists():
        shutil.copy2(P, bak)
        print(f"backup -> {bak.name}")
    P.write_text(text)
    import ast
    try:
        ast.parse(P.read_text(), str(P))
        print("AST ok")
    except SyntaxError as e:
        print(f"AST FAIL: {e}", file=sys.stderr)
        return 3

    # Surface in the OpenAI-compatible response too — the patch in 01 wraps
    # the dict with breakdown; we add last_prompt_tokens alongside.
    text = P.read_text()
    api_old = '                **({"breakdown": usage["breakdown"]} if usage.get("breakdown") else {}),\n'
    api_new = (
        '                **({"breakdown": usage["breakdown"]} if usage.get("breakdown") else {}),\n'
        '                **({"last_prompt_tokens": usage["last_prompt_tokens"]} if usage.get("last_prompt_tokens") else {}),\n'
    )
    n2 = text.count(api_old)
    if n2 > 0:
        text = text.replace(api_old, api_new)
        P.write_text(text)
        print(f"  exposed last_prompt_tokens in {n2} response location(s)")
    else:
        print("WARN: response anchor not found", file=sys.stderr)

    print("patched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
