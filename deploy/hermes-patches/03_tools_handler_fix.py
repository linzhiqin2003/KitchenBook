"""Fix /api/tools 500 by replacing the missing _load_tools_config import
with _get_effective_configurable_toolsets, which exists in this Hermes
build and returns the (key, label, desc) tuples we need.

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "_get_effective_configurable_toolsets"


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("[skip] already patched")
        return 0
    old = (
        "    async def _handle_list_tools(self, request: \"web.Request\") -> \"web.Response\":\n"
        "        \"\"\"GET /api/tools — list toolsets and their enabled/disabled status.\"\"\"\n"
        "        from hermes_cli.tools_config import _get_platform_tools, _load_tools_config\n"
        "        from gateway.run import _load_gateway_config\n"
        "\n"
        "        user_config = _load_gateway_config()\n"
        "        enabled = set(_get_platform_tools(user_config, \"api_server\"))\n"
        "\n"
        "        # Get all available toolsets\n"
        "        tools_config = _load_tools_config()\n"
        "        all_toolsets = tools_config.get(\"toolsets\", {})\n"
        "\n"
        "        result = []\n"
        "        for name, info in sorted(all_toolsets.items()):\n"
        "            result.append({\n"
        "                \"name\": name,\n"
        "                \"description\": info.get(\"description\", \"\"),\n"
        "                \"enabled\": name in enabled,\n"
        "                \"type\": \"builtin\",\n"
        "            })\n"
    )
    new = (
        "    async def _handle_list_tools(self, request: \"web.Request\") -> \"web.Response\":\n"
        "        \"\"\"GET /api/tools — list toolsets and their enabled/disabled status.\"\"\"\n"
        "        from hermes_cli.tools_config import (\n"
        "            _get_platform_tools,\n"
        "            _get_effective_configurable_toolsets,\n"
        "        )\n"
        "        from gateway.run import _load_gateway_config\n"
        "\n"
        "        user_config = _load_gateway_config()\n"
        "        enabled = set(_get_platform_tools(user_config, \"api_server\"))\n"
        "\n"
        "        # Built-in (and plugin-provided) toolsets surface as (key, label, detail) tuples.\n"
        "        result = []\n"
        "        for name, label, detail in _get_effective_configurable_toolsets():\n"
        "            result.append({\n"
        "                \"name\": name,\n"
        "                \"description\": label,\n"
        "                \"detail\": detail,\n"
        "                \"enabled\": name in enabled,\n"
        "                \"type\": \"builtin\",\n"
        "            })\n"
    )
    if old not in text:
        print("FATAL: anchor not found", file=sys.stderr)
        return 2
    if text.count(old) != 1:
        print(f"FATAL: anchor matched {text.count(old)} times", file=sys.stderr)
        return 2
    bak = P.with_suffix(P.suffix + ".tools.bak")
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
