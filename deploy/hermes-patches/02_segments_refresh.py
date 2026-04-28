"""Fix: when restoring a cached system prompt from session DB, also
re-run _build_system_prompt for its side-effect of populating
self._prompt_segments — otherwise compute_prompt_breakdown() returns
only the tools/messages buckets and the UI shows a degenerate panel.

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/run_agent.py")
MARKER = "# breakdown: keep _prompt_segments fresh on restored sessions"


def main() -> int:
    text = P.read_text()
    if MARKER in text:
        print("[skip] already patched")
        return 0
    old = (
        "            if stored_prompt:\n"
        "                # Continuing session — reuse the exact system prompt from\n"
        "                # the previous turn so the Anthropic cache prefix matches.\n"
        "                self._cached_system_prompt = stored_prompt\n"
    )
    new = (
        "            if stored_prompt:\n"
        "                # Continuing session — reuse the exact system prompt from\n"
        "                # the previous turn so the Anthropic cache prefix matches.\n"
        "                self._cached_system_prompt = stored_prompt\n"
        "                " + MARKER + "\n"
        "                try:\n"
        "                    # Side-effect only: refresh self._prompt_segments so the\n"
        "                    # /v1 usage.breakdown response keeps every bucket populated\n"
        "                    # (identity / skills / memory / context / env_meta).  We\n"
        "                    # discard the returned flat string to preserve cache prefix.\n"
        "                    self._build_system_prompt(system_message)\n"
        "                    self._cached_system_prompt = stored_prompt\n"
        "                except Exception as _exc:\n"
        "                    logger.debug(\"rebuild segments for breakdown failed: %s\", _exc)\n"
    )
    if old not in text:
        print("FATAL: anchor not found", file=sys.stderr)
        return 2
    if text.count(old) != 1:
        print(f"FATAL: anchor matched {text.count(old)} times; expected 1", file=sys.stderr)
        return 2
    bak = P.with_suffix(P.suffix + ".segments.bak")
    if not bak.exists():
        shutil.copy2(P, bak)
        print(f"backup -> {bak.name}")
    P.write_text(text.replace(old, new))
    import ast
    try:
        ast.parse(P.read_text(), str(P))
        print("AST ok")
    except SyntaxError as e:
        print(f"AST FAIL: {e}", file=sys.stderr)
        return 3
    print("patched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
