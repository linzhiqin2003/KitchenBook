"""Honor X-Hermes-History-Source: request header to use messages from
the request body instead of state.db's stored history.

When the frontend edits or regenerates a message, it deletes the
relevant turns from Django and re-sends a truncated messages list.
Hermes' default behavior — when X-Hermes-Session-Id is present — is
to discard the request body's messages and load history from its own
state.db. That state.db still has the deleted turns, so the agent
sees the old context and the UI / agent diverge.

Add an opt-in header that lets the client say "trust my messages
array, don't pull stored history". Default behavior unchanged.

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "X-Hermes-History-Source"


OLD_BLOCK = (
    '            session_id = provided_session_id\n'
    '            try:\n'
    '                db = self._ensure_session_db()\n'
    '                if db is not None:\n'
    '                    history = db.get_messages_as_conversation(session_id)\n'
    '            except Exception as e:\n'
    '                logger.warning("Failed to load session history for %s: %s", session_id, e)\n'
    '                history = []\n'
)

NEW_BLOCK = (
    '            session_id = provided_session_id\n'
    '            # Opt-out of stored-history load via X-Hermes-History-Source: request.\n'
    '            # Frontend sets this on edit / regenerate so the truncated messages\n'
    '            # array in the request body is authoritative — otherwise Hermes\n'
    '            # would replay deleted turns from its state.db cache.\n'
    '            history_source = (request.headers.get("X-Hermes-History-Source") or "").strip().lower()\n'
    '            if history_source == "request":\n'
    '                logger.info(\n'
    '                    "Session %s: using request-body messages (X-Hermes-History-Source=request)",\n'
    '                    session_id,\n'
    '                )\n'
    '                # `history` already populated from request body further up; keep it.\n'
    '            else:\n'
    '                try:\n'
    '                    db = self._ensure_session_db()\n'
    '                    if db is not None:\n'
    '                        history = db.get_messages_as_conversation(session_id)\n'
    '                except Exception as e:\n'
    '                    logger.warning("Failed to load session history for %s: %s", session_id, e)\n'
    '                    history = []\n'
)


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("[skip] already patched")
        return 0
    if OLD_BLOCK not in text:
        print("FATAL: anchor not found", file=sys.stderr)
        return 2
    text = text.replace(OLD_BLOCK, NEW_BLOCK)

    bak = P.with_suffix(P.suffix + ".histsrc.bak")
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
