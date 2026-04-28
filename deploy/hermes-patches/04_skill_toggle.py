"""Add POST /api/skills/toggle endpoint to Hermes API server.

Lets the AI Lab right-side panel enable/disable individual skills the
same way it already toggles toolsets.  Persists to
``~/.hermes/config.yaml`` under ``skills.disabled`` which is what
``agent.skill_utils.get_disabled_skill_names()`` reads when building
the system prompt, so toggles take effect on the next chat request.

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "_handle_toggle_skill"


HANDLER = '''    async def _handle_toggle_skill(self, request: "web.Request") -> "web.Response":
        """POST /api/skills/toggle — body: {name, enable}.

        Persists to ``~/.hermes/config.yaml`` under ``skills.disabled``;
        next chat request rebuilds the system prompt and reflects the change.
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "invalid JSON"}, status=400)
        name = body.get("name")
        if not name or not isinstance(name, str):
            return web.json_response({"error": "name required"}, status=400)
        enable = bool(body.get("enable", True))

        import yaml as _yaml
        config_path = os.path.expanduser("~/.hermes/config.yaml")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = _yaml.safe_load(f) or {}
        except FileNotFoundError:
            cfg = {}
        except Exception as e:
            return web.json_response({"error": f"read config failed: {e}"}, status=500)

        if not isinstance(cfg, dict):
            cfg = {}
        skills_cfg = cfg.get("skills")
        if not isinstance(skills_cfg, dict):
            skills_cfg = {}
            cfg["skills"] = skills_cfg

        raw_disabled = skills_cfg.get("disabled") or []
        if not isinstance(raw_disabled, list):
            raw_disabled = []
        disabled = [str(d) for d in raw_disabled if isinstance(d, (str, int))]

        if enable:
            disabled = [d for d in disabled if d != name]
        else:
            if name not in disabled:
                disabled.append(name)

        skills_cfg["disabled"] = disabled

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            return web.json_response({"error": f"write config failed: {e}"}, status=500)

        return web.json_response({"name": name, "enabled": enable})

'''


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("[skip] already patched")
        return 0

    # Insert handler right after _handle_list_skills' second definition closes.
    # Anchor: find the line "return web.json_response({\"skills\": skills})\n\n    async def _handle_get_memory"
    anchor = (
        "        return web.json_response({\"skills\": skills})\n"
        "\n"
        "    async def _handle_get_memory(self, request: \"web.Request\") -> \"web.Response\":\n"
    )
    if anchor not in text:
        print("FATAL: anchor for handler insertion not found", file=sys.stderr)
        return 2
    # The user's local Lab Panel mod accidentally duplicated _handle_list_skills
    # and _handle_get_memory in the same class.  Methods later in the file shadow
    # earlier ones in Python, so insert the new handler before the LAST anchor —
    # that's the live definition.  Inserting only once keeps the class clean.
    new_block = (
        "        return web.json_response({\"skills\": skills})\n"
        "\n"
        + HANDLER
        + "    async def _handle_get_memory(self, request: \"web.Request\") -> \"web.Response\":\n"
    )
    last_idx = text.rfind(anchor)
    text = text[:last_idx] + new_block + text[last_idx + len(anchor):]
    print(f"  handler injected before last of {text.count('async def _handle_list_skills')} _handle_list_skills defs")

    # Register the route — inject right after the existing /api/skills GET.
    # There are TWO router.add_get("/api/skills", ...) blocks (likely one
    # gated by a flag); patch both.
    route_old = "self._app.router.add_get(\"/api/skills\", self._handle_list_skills)\n"
    route_new = (
        "self._app.router.add_get(\"/api/skills\", self._handle_list_skills)\n"
        "            self._app.router.add_post(\"/api/skills/toggle\", self._handle_toggle_skill)\n"
    )
    count = text.count(route_old)
    if count == 0:
        print("FATAL: skills route anchor not found", file=sys.stderr)
        return 2
    text = text.replace(route_old, route_new)
    print(f"  routes injected (matched {count} occurrence(s))")

    bak = P.with_suffix(P.suffix + ".skilltoggle.bak")
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
