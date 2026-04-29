"""Per-user isolation for the AI Lab integration.

The frontend now sends ``X-Hermes-User-Id`` on every request from a
logged-in user.  This patch makes Hermes:

1. Read the header on every gateway HTTP request and stash the value
   into the ``HERMES_SESSION_USER_ID`` contextvar so concurrent users
   never alias each other.
2. Override ``tools.memory_tool.get_memory_dir`` and the
   ``hermes_constants.get_config_path`` references so when a user-id
   is set the agent reads/writes:
       <hermes_home>/users/<user_id>/memories/MEMORY.md
       <hermes_home>/users/<user_id>/memories/USER.md
       <hermes_home>/users/<user_id>/config.yaml
   instead of the global files.  Anonymous (no header) requests fall
   back to the original global paths so CLI / cron usage is unaffected.

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "_install_per_user_path_overrides"


# ── 1. Module-level helper that installs path overrides + a middleware that
#    pulls X-Hermes-User-Id off every request and binds it to the contextvar.
HELPER_BLOCK = '''
def _install_per_user_path_overrides() -> None:
    """Monkey-patch memory + config path resolution so paths scope to the
    current ``HERMES_SESSION_USER_ID`` contextvar.

    Runs once at module load.  The wrapped originals are kept so the
    fallback (anonymous / CLI use) returns the global path unchanged.
    """
    try:
        import tools.memory_tool as _mem_mod
    except Exception:
        return  # tools package may be absent in some test contexts
    try:
        import hermes_constants as _hc
    except Exception:
        _hc = None
    try:
        import agent.skill_utils as _su
    except Exception:
        _su = None

    if getattr(_mem_mod, "_per_user_isolation_installed", False):
        return  # idempotent — re-running this patch on deploy is fine

    from gateway.session_context import get_session_env as _get_session_env
    from pathlib import Path as _Path

    _orig_get_memory_dir = _mem_mod.get_memory_dir
    _orig_get_hermes_home = None
    if _hc is not None:
        _orig_get_hermes_home = _hc.get_hermes_home

    def _user_scope_root() -> "_Path | None":
        """Return ``<hermes_home>/users/<user_id>/`` if a user-id is bound,
        otherwise None (caller should use the global path)."""
        uid = (_get_session_env("HERMES_SESSION_USER_ID", "") or "").strip()
        if not uid:
            return None
        # Defensive: limit to a safe filename charset so a malicious header
        # cannot path-traverse out of the user dir.
        import re as _re
        if not _re.fullmatch(r"[A-Za-z0-9_\\-]+", uid):
            return None
        if _orig_get_hermes_home is None:
            home = _orig_get_memory_dir().parent  # fallback: hermes_home from memory dir parent
        else:
            home = _orig_get_hermes_home()
        return _Path(home) / "users" / uid

    def _scoped_memory_dir() -> "_Path":
        root = _user_scope_root()
        if root is None:
            return _orig_get_memory_dir()
        d = root / "memories"
        d.mkdir(parents=True, exist_ok=True)
        return d

    _mem_mod.get_memory_dir = _scoped_memory_dir

    if _hc is not None and hasattr(_hc, "get_config_path"):
        _orig_get_config_path = _hc.get_config_path

        def _scoped_config_path() -> "_Path":
            root = _user_scope_root()
            if root is None:
                return _orig_get_config_path()
            root.mkdir(parents=True, exist_ok=True)
            return root / "config.yaml"

        _hc.get_config_path = _scoped_config_path
        # ``agent.skill_utils`` did ``from hermes_constants import get_config_path``
        # at import time, capturing a reference to the original.  Reassign that
        # bound name so skill_utils picks up the scoped version too.
        if _su is not None and hasattr(_su, "get_config_path"):
            _su.get_config_path = _scoped_config_path

    _mem_mod._per_user_isolation_installed = True


_install_per_user_path_overrides()


@web.middleware
async def _per_user_session_middleware(request, handler):
    """Bind ``X-Hermes-User-Id`` and ``X-Hermes-Session-Id`` headers to the
    request-scoped contextvars before dispatching the handler.

    Uses the same ``set_session_vars`` / ``clear_session_vars`` pair the
    messaging adapters already use, so concurrency is contextvar-safe.
    """
    from gateway.session_context import set_session_vars, clear_session_vars
    user_id = (request.headers.get("X-Hermes-User-Id") or "").strip()
    session_id = (request.headers.get("X-Hermes-Session-Id") or "").strip()
    tokens = set_session_vars(
        platform="api_server",
        user_id=user_id,
        session_key=session_id,
    )
    try:
        return await handler(request)
    finally:
        clear_session_vars(tokens)
'''


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("[skip] already patched")
        return 0

    # 1) Insert helper block + middleware factory just before the
    #    APIServerAdapter class.
    anchor = "class APIServerAdapter(BasePlatformAdapter):"
    if text.count(anchor) != 1:
        print(f"FATAL: expected 1 APIServerAdapter, found {text.count(anchor)}", file=sys.stderr)
        return 2
    text = text.replace(anchor, HELPER_BLOCK + "\n" + anchor, 1)

    # 2) Register the middleware on the aiohttp app.  We anchor on a stable
    #    line near the route registrations and inject above it.
    route_anchor = '            self._app.router.add_get("/api/tools", self._handle_list_tools)\n'
    middleware_inject = (
        '            # AI Lab per-user isolation: bind X-Hermes-User-Id header to contextvar\n'
        '            try:\n'
        '                if _per_user_session_middleware not in self._app.middlewares:\n'
        '                    self._app.middlewares.append(_per_user_session_middleware)\n'
        '            except Exception:\n'
        '                pass\n'
    )
    count = text.count(route_anchor)
    if count == 0:
        print("FATAL: route anchor not found", file=sys.stderr)
        return 2
    # Inject the middleware registration once before the FIRST occurrence only —
    # the user mod has two route-registration blocks but they share the same
    # ``self._app`` instance, so registering the middleware once is enough.
    first_idx = text.find(route_anchor)
    text = text[:first_idx] + middleware_inject + text[first_idx:]
    print(f"  middleware registered ({count} route block(s) seen, registered once)")

    # 3) Propagate contextvars (HERMES_SESSION_USER_ID etc.) into the executor
    #    thread that runs the synchronous agent.  Plain ``run_in_executor(None, _run)``
    #    does NOT carry contextvars across the thread boundary, so without this
    #    the per-user path overrides see an empty user-id and fall back to the
    #    global memory dir.
    exec_old = "        return await loop.run_in_executor(None, _run)\n"
    exec_new = (
        "        # Propagate contextvars (HERMES_SESSION_USER_ID set by the\n"
        "        # _per_user_session_middleware) into the executor thread —\n"
        "        # naked run_in_executor would otherwise drop them.\n"
        "        import contextvars as _ctxvars\n"
        "        _ctx = _ctxvars.copy_context()\n"
        "        return await loop.run_in_executor(None, lambda: _ctx.run(_run))\n"
    )
    if exec_old in text:
        text = text.replace(exec_old, exec_new, 1)
        print("  executor wrapped with copy_context")
    else:
        print("WARN: executor anchor not found — contextvars may not propagate", file=sys.stderr)

    bak = P.with_suffix(P.suffix + ".peruser.bak")
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
