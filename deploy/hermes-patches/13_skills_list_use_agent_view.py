"""Make GET /api/skills show what the agent actually sees.

Bug: the fallback in _handle_list_skills walks the skills/ directory
and emits every SKILL.md it finds, irrespective of the skill's
``platforms:`` frontmatter.  On a Linux server that means the panel
lists macOS-only skills (apple-notes, apple-reminders, findmy,
imessage, …) as ``enabled: True`` even though the agent's own
skills_list / skills_get tools never see them — they're filtered out
by ``skill_matches_platform()`` in tools/skills_tool.py.

This patch rewrites both copies of _handle_list_skills to call
``_find_all_skills(skip_disabled=True)`` first (the same function the
agent uses).  That gets us the platform-filtered list with each
skill's full frontmatter-derived metadata.  We then read
config.yaml::skills.disabled and flip ``enabled`` to False for any
toggled-off skill, preserving patch11's behaviour.

Idempotent — keyed off SENTINEL appearing in the file."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "# [patch13] use agent's filtered skill view"

OLD = '''        """GET /api/skills — list installed skills."""
        import subprocess
        try:
            result = subprocess.run(
                [os.path.expanduser("~/.local/bin/hermes"), "skills", "list", "--json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                skills = json.loads(result.stdout)
                return web.json_response({"skills": skills})
        except Exception:
            pass

        # Fallback: read skills directory
        skills_dir = os.path.expanduser("~/.hermes/skills")
        skills = []
        if os.path.isdir(skills_dir):
            for category in sorted(os.listdir(skills_dir)):
                cat_path = os.path.join(skills_dir, category)
                if os.path.isdir(cat_path):
                    for skill_name in sorted(os.listdir(cat_path)):
                        skill_path = os.path.join(cat_path, skill_name)
                        if os.path.isdir(skill_path) and os.path.exists(os.path.join(skill_path, "SKILL.md")):
                            skills.append({
                                "name": skill_name,
                                "category": category,
                                "path": skill_path,
                                "enabled": not os.path.exists(os.path.join(skill_path, ".disabled")),
                            })
                    # Also check if category itself is a skill
                    if os.path.exists(os.path.join(cat_path, "SKILL.md")):
                        skills.append({
                            "name": category,
                            "category": "",
                            "path": cat_path,
                            "enabled": not os.path.exists(os.path.join(cat_path, ".disabled")),
                        })

        # [patch11] apply yaml-disabled list — toggle handler writes
        # config.yaml under skills.disabled, so honour that here.
        try:
            import yaml as _yaml_p11
            _cfg_p11_path = os.path.expanduser("~/.hermes/config.yaml")
            with open(_cfg_p11_path, "r", encoding="utf-8") as _f_p11:
                _cfg_p11 = _yaml_p11.safe_load(_f_p11) or {}
            _raw_p11 = (_cfg_p11.get("skills") or {}).get("disabled") or []
            _disabled_p11 = {str(_d) for _d in _raw_p11 if isinstance(_d, (str, int))}
            for _s_p11 in skills:
                if _s_p11.get("name") in _disabled_p11:
                    _s_p11["enabled"] = False
        except Exception:
            pass

        return web.json_response({"skills": skills})'''

NEW = '''        """GET /api/skills — list installed skills."""
        # [patch13] use agent's filtered skill view — call the same
        # _find_all_skills() the skills_list tool uses so that platform
        # filtering (frontmatter ``platforms:`` field) is consistent.
        # Otherwise the panel shows e.g. macOS-only skills as enabled on
        # a Linux host, even though the agent can never actually invoke
        # them.
        skills = []
        try:
            from tools.skills_tool import _find_all_skills
            raw = _find_all_skills(skip_disabled=True)
            for s in raw:
                skills.append({
                    "name": s.get("name"),
                    "category": s.get("category", ""),
                    "description": s.get("description", ""),
                    "enabled": True,
                })
        except Exception:
            # Defensive fallback: directory walk (may include skills the
            # agent can't actually run, but better than nothing).
            skills_dir = os.path.expanduser("~/.hermes/skills")
            if os.path.isdir(skills_dir):
                for category in sorted(os.listdir(skills_dir)):
                    cat_path = os.path.join(skills_dir, category)
                    if os.path.isdir(cat_path):
                        for skill_name in sorted(os.listdir(cat_path)):
                            skill_path = os.path.join(cat_path, skill_name)
                            if os.path.isdir(skill_path) and os.path.exists(os.path.join(skill_path, "SKILL.md")):
                                skills.append({
                                    "name": skill_name,
                                    "category": category,
                                    "enabled": True,
                                })
                        if os.path.exists(os.path.join(cat_path, "SKILL.md")):
                            skills.append({
                                "name": category,
                                "category": "",
                                "enabled": True,
                            })

        # Apply yaml-disabled list — toggle handler writes config.yaml
        # under skills.disabled, so honour that here (formerly patch 11).
        try:
            import yaml as _yaml_p13
            _cfg_p13_path = os.path.expanduser("~/.hermes/config.yaml")
            with open(_cfg_p13_path, "r", encoding="utf-8") as _f_p13:
                _cfg_p13 = _yaml_p13.safe_load(_f_p13) or {}
            _raw_p13 = (_cfg_p13.get("skills") or {}).get("disabled") or []
            _disabled_p13 = {str(_d) for _d in _raw_p13 if isinstance(_d, (str, int))}
            for _s_p13 in skills:
                if _s_p13.get("name") in _disabled_p13:
                    _s_p13["enabled"] = False
        except Exception:
            pass

        return web.json_response({"skills": skills})'''


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("  [skip] already patched")
        return 0
    if OLD not in text:
        print("FATAL: anchor not found", file=sys.stderr)
        return 2
    count = text.count(OLD)
    if count not in (1, 2):
        print(f"FATAL: anchor matched {count} times (expected 1 or 2)", file=sys.stderr)
        return 2
    bak = P.with_suffix(P.suffix + ".skillsview.bak")
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
        shutil.copy2(bak, P)
        return 3
    print(f"  patched (replaced {count} occurrence{'s' if count > 1 else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
