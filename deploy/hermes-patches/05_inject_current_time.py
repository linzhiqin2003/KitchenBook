"""Inject the current wall-clock time (Europe/London) into every
agent's ephemeral system prompt so the model can answer "what time is
it" without hallucinating.

The ephemeral channel is the right place: Hermes appends it to the
flat system prompt at API-call time but does NOT bake it into the
cached prefix, so we get fresh time on every turn without busting the
Anthropic prompt cache.

Override the timezone by setting ``HERMES_AGENT_TZ`` in the gateway's
env (e.g. ``Europe/London``, ``America/New_York``, ``UTC``).  Defaults
to ``Europe/London``.

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "_with_current_time_block"


HELPER = '''
def _with_current_time_block(ephemeral: "str | None") -> "str | None":
    """Prepend a fresh wall-clock line to ``ephemeral`` so the agent
    knows the current time on every chat-completion call.

    Picks up timezone from the ``HERMES_AGENT_TZ`` env var (default
    ``Europe/London``).  Falls back to server-local time if the
    requested zone is unavailable.
    """
    import os as _os
    from datetime import datetime as _dt
    tz_name = _os.environ.get("HERMES_AGENT_TZ", "Europe/London")
    try:
        from zoneinfo import ZoneInfo as _ZI
        now = _dt.now(_ZI(tz_name))
        stamp = now.strftime("%A, %B %d, %Y %I:%M %p %Z").strip()
        block = f"Current time: {stamp} ({tz_name})."
    except Exception:
        now = _dt.now()
        stamp = now.strftime("%A, %B %d, %Y %I:%M %p")
        block = f"Current time: {stamp} (server local)."
    if ephemeral and ephemeral.strip():
        return block + "\\n\\n" + ephemeral
    return block

'''


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("[skip] already patched")
        return 0

    # 1) Insert helper just before the APIServerAdapter class definition.
    anchor = "class APIServerAdapter(BasePlatformAdapter):"
    if text.count(anchor) != 1:
        print(f"FATAL: expected 1 APIServerAdapter class, found {text.count(anchor)}", file=sys.stderr)
        return 2
    text = text.replace(anchor, HELPER + "\n" + anchor, 1)

    # 2) In _create_agent, wrap ephemeral_system_prompt with the helper.
    #    The line we anchor on must be unique; both occurrences (if any)
    #    of the same literal would replace, which is exactly what we want
    #    if the codebase had multiple agents — but here it's just one.
    old_line = "            ephemeral_system_prompt=ephemeral_system_prompt or None,"
    new_line = "            ephemeral_system_prompt=_with_current_time_block(ephemeral_system_prompt or None),"
    count = text.count(old_line)
    if count == 0:
        print("FATAL: ephemeral_system_prompt assignment not found", file=sys.stderr)
        return 2
    text = text.replace(old_line, new_line)
    print(f"  wrapped ephemeral assignment ({count} occurrence(s))")

    bak = P.with_suffix(P.suffix + ".curtime.bak")
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
    print("patched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
