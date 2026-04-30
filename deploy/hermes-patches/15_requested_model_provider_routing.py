"""Route selected API-server models through the correct Hermes provider.

Background:
  - Patch 14 threads `body["model"]` through to `_create_agent()`, so the
    gateway now honors per-request model overrides.
  - Runtime credentials still come from `_resolve_runtime_agent_kwargs()`,
    which follows the gateway's configured default provider. That means a
    request for `xiaomi/...` would still inherit the DeepSeek runtime unless
    we override provider resolution as well.

This patch keeps current DeepSeek behavior unchanged, but maps selected model
families to the runtime provider they require. Today:
  - `xiaomi/...` -> OpenRouter

Idempotent.
"""

from __future__ import annotations

import ast
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "def _resolve_requested_runtime_provider(requested_model: Optional[str]) -> Optional[str]:"


def backup_once(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".request-provider.bak")
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
        "def _with_current_time_block(ephemeral: \"str | None\") -> \"str | None\":\n",
        "def _resolve_requested_runtime_provider(requested_model: Optional[str]) -> Optional[str]:\n"
        "    requested = (requested_model or \"\").strip().lower() if isinstance(requested_model, str) else \"\"\n"
        "    if requested.startswith(\"xiaomi/\"):\n"
        "        return \"openrouter\"\n"
        "    return None\n\n"
        "def _with_current_time_block(ephemeral: \"str | None\") -> \"str | None\":\n",
        "provider routing helper",
    )

    text = apply_replace(
        text,
        "        runtime_kwargs = _resolve_runtime_agent_kwargs()\n"
        "        requested = (requested_model or \"\").strip() if isinstance(requested_model, str) else \"\"\n"
        "        model = requested if requested and requested not in {\"hermes-agent\", self._model_name} else _resolve_gateway_model()\n",
        "        runtime_kwargs = _resolve_runtime_agent_kwargs()\n"
        "        requested = (requested_model or \"\").strip() if isinstance(requested_model, str) else \"\"\n"
        "        model = requested if requested and requested not in {\"hermes-agent\", self._model_name} else _resolve_gateway_model()\n"
        "        requested_provider = _resolve_requested_runtime_provider(requested)\n"
        "        if requested_provider and runtime_kwargs.get(\"provider\") != requested_provider:\n"
        "            from hermes_cli.runtime_provider import resolve_runtime_provider\n"
        "            requested_runtime = resolve_runtime_provider(\n"
        "                requested=requested_provider,\n"
        "                target_model=model,\n"
        "            )\n"
        "            runtime_kwargs.update({\n"
        "                \"api_key\": requested_runtime.get(\"api_key\"),\n"
        "                \"base_url\": requested_runtime.get(\"base_url\"),\n"
        "                \"provider\": requested_runtime.get(\"provider\"),\n"
        "                \"api_mode\": requested_runtime.get(\"api_mode\"),\n"
        "            })\n",
        "_create_agent runtime provider override",
    )

    P.write_text(text)
    try:
        ast.parse(P.read_text(), str(P))
    except SyntaxError as exc:
        print(f"AST FAIL: {exc}", file=sys.stderr)
        return 3
    print("AST ok")
    print("patched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
