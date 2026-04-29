"""Let API clients choose the underlying Hermes model per request/session.

Background:
  - `run_agent.py` already supports model switching.
  - The OpenAI-compatible API adapter currently reads `body["model"]` only
    for response metadata, but still instantiates AIAgent with the gateway's
    configured default model.

This patch threads the request model through `_handle_chat_completions` /
`_handle_responses` -> `_run_agent` -> `_create_agent`, while keeping
`hermes-agent` (or the adapter's advertised model alias) as a route alias
for "use the configured default model".

Idempotent.
"""

from __future__ import annotations

import ast
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "requested_model: Optional[str] = None,"


def backup_once(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".request-model.bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"backup -> {bak.name}")


def apply_replace(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"[skip] {label}")
        return text
    if old not in text:
        raise SystemExit(f"FATAL: anchor not found for {label}")
    return text.replace(old, new, 1)


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("[skip] already patched")
        return 0

    backup_once(P)

    text = apply_replace(
        text,
        "        ephemeral_system_prompt: Optional[str] = None,\n"
        "        session_id: Optional[str] = None,\n"
        "        stream_delta_callback=None,\n",
        "        ephemeral_system_prompt: Optional[str] = None,\n"
        "        session_id: Optional[str] = None,\n"
        "        requested_model: Optional[str] = None,\n"
        "        stream_delta_callback=None,\n",
        "_create_agent signature",
    )

    text = apply_replace(
        text,
        "        runtime_kwargs = _resolve_runtime_agent_kwargs()\n"
        "        model = _resolve_gateway_model()\n",
        "        runtime_kwargs = _resolve_runtime_agent_kwargs()\n"
        "        requested = (requested_model or \"\").strip() if isinstance(requested_model, str) else \"\"\n"
        "        model = requested if requested and requested not in {\"hermes-agent\", self._model_name} else _resolve_gateway_model()\n",
        "_create_agent requested model",
    )

    text = apply_replace(
        text,
        "        ephemeral_system_prompt: Optional[str] = None,\n"
        "        session_id: Optional[str] = None,\n"
        "        stream_delta_callback=None,\n",
        "        ephemeral_system_prompt: Optional[str] = None,\n"
        "        session_id: Optional[str] = None,\n"
        "        model_name: Optional[str] = None,\n"
        "        stream_delta_callback=None,\n",
        "_run_agent signature",
    )

    text = apply_replace(
        text,
        "            agent = self._create_agent(\n"
        "                ephemeral_system_prompt=ephemeral_system_prompt,\n"
        "                session_id=session_id,\n"
        "                stream_delta_callback=stream_delta_callback,\n",
        "            agent = self._create_agent(\n"
        "                ephemeral_system_prompt=ephemeral_system_prompt,\n"
        "                session_id=session_id,\n"
        "                requested_model=model_name,\n"
        "                stream_delta_callback=stream_delta_callback,\n",
        "_run_agent -> _create_agent",
    )

    text = apply_replace(
        text,
        "                ephemeral_system_prompt=system_prompt,\n"
        "                session_id=session_id,\n"
        "                stream_delta_callback=_on_delta,\n",
        "                ephemeral_system_prompt=system_prompt,\n"
        "                session_id=session_id,\n"
        "                model_name=model_name,\n"
        "                stream_delta_callback=_on_delta,\n",
        "chat streaming call",
    )

    text = apply_replace(
        text,
        "                user_message=user_message,\n"
        "                conversation_history=history,\n"
        "                ephemeral_system_prompt=system_prompt,\n"
        "                session_id=session_id,\n"
        "            )\n",
        "                user_message=user_message,\n"
        "                conversation_history=history,\n"
        "                ephemeral_system_prompt=system_prompt,\n"
        "                session_id=session_id,\n"
        "                model_name=model_name,\n"
        "            )\n",
        "chat non-streaming call",
    )

    text = apply_replace(
        text,
        "                ephemeral_system_prompt=instructions,\n"
        "                session_id=session_id,\n"
        "                stream_delta_callback=_on_delta,\n",
        "                ephemeral_system_prompt=instructions,\n"
        "                session_id=session_id,\n"
        "                model_name=body.get(\"model\", self._model_name),\n"
        "                stream_delta_callback=_on_delta,\n",
        "responses streaming call",
    )

    text = apply_replace(
        text,
        "                conversation_history=conversation_history,\n"
        "                ephemeral_system_prompt=instructions,\n"
        "                session_id=session_id,\n"
        "            )\n",
        "                conversation_history=conversation_history,\n"
        "                ephemeral_system_prompt=instructions,\n"
        "                session_id=session_id,\n"
        "                model_name=body.get(\"model\", self._model_name),\n"
        "            )\n",
        "responses non-streaming call",
    )

    P.write_text(text)
    try:
      ast.parse(P.read_text(), str(P))
    except SyntaxError as e:
      print(f"AST FAIL: {e}", file=sys.stderr)
      return 3
    print("AST ok")
    print("patched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
