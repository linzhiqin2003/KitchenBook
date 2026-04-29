"""Make GET /api/skills reflect the actual disabled list.

Hermes' built-in toggle endpoint persists the off-list to
``~/.hermes/config.yaml`` under ``skills.disabled`` (see 04_skill_toggle.py
and base hermes ``agent.skill_utils.get_disabled_skill_names``).  But the
matching list endpoint (`_handle_list_skills`) only checks for a
``.disabled`` sentinel file inside each skill directory — a path the
toggle handler never writes — so toggled-off skills always come back as
``enabled: true`` on the next list call.

Patch both copies of the handler (there are two declared in the same
class; the second one wins at class-creation time, but we patch both so
the diff is consistent and a future refactor that drops one doesn't
silently regress).  Right before the final ``return``, read
``config.yaml`` and force ``enabled = False`` for any skill whose name
appears in ``skills.disabled``.

Idempotent — keyed off SENTINEL appearing in the file."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "# [patch11] apply yaml-disabled list"
# patch13 rewrote the whole _handle_list_skills body and folded patch11's
# disabled-list overlay into its own NEW block, so its presence means we're
# also covered.
SENTINEL_SUPERSEDED = "# [patch13] use agent's filtered skill view"

OLD = (
    "                            \"enabled\": not os.path.exists(os.path.join(cat_path, \".disabled\")),\n"
    "                        })\n"
    "\n"
    "        return web.json_response({\"skills\": skills})\n"
)

NEW = (
    "                            \"enabled\": not os.path.exists(os.path.join(cat_path, \".disabled\")),\n"
    "                        })\n"
    "\n"
    "        # [patch11] apply yaml-disabled list — toggle handler writes\n"
    "        # config.yaml under skills.disabled, so honour that here.\n"
    "        try:\n"
    "            import yaml as _yaml_p11\n"
    "            _cfg_p11_path = os.path.expanduser(\"~/.hermes/config.yaml\")\n"
    "            with open(_cfg_p11_path, \"r\", encoding=\"utf-8\") as _f_p11:\n"
    "                _cfg_p11 = _yaml_p11.safe_load(_f_p11) or {}\n"
    "            _raw_p11 = (_cfg_p11.get(\"skills\") or {}).get(\"disabled\") or []\n"
    "            _disabled_p11 = {str(_d) for _d in _raw_p11 if isinstance(_d, (str, int))}\n"
    "            for _s_p11 in skills:\n"
    "                if _s_p11.get(\"name\") in _disabled_p11:\n"
    "                    _s_p11[\"enabled\"] = False\n"
    "        except Exception:\n"
    "            pass\n"
    "\n"
    "        return web.json_response({\"skills\": skills})\n"
)


def main() -> int:
    text = P.read_text()
    if SENTINEL in text or SENTINEL_SUPERSEDED in text:
        print("  [skip] already patched")
        return 0
    if OLD not in text:
        print("FATAL: anchor not found", file=sys.stderr)
        return 2
    count = text.count(OLD)
    if count not in (1, 2):
        print(f"FATAL: anchor matched {count} times (expected 1 or 2)", file=sys.stderr)
        return 2
    bak = P.with_suffix(P.suffix + ".skillslist.bak")
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
        # Restore from backup on AST failure
        shutil.copy2(bak, P)
        return 3
    print(f"  patched (replaced {count} occurrence{'s' if count > 1 else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
