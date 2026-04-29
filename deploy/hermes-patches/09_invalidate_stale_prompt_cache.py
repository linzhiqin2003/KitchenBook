"""Auto-invalidate the cached system_prompt when the user's memory or
config files have changed.

Hermes stores each session's assembled system_prompt in state.db so
subsequent turns can reuse it (Anthropic prompt-cache prefix matching).
But that means edits to USER.md / MEMORY.md / config.yaml don't reach
the agent until the cache is manually cleared — which is exactly what
just bit us when notification API instructions appended to USER.md
weren't visible to the agent.

This patch tracks the per-session "built at" time via a sentinel file
under ``$HERMES_HOME/_prompt_cache/<session_id>.built`` (touched when
the prompt is freshly assembled).  On the load path, if any of the
relevant memory sources has a newer mtime than the sentinel, we ignore
the stored_prompt and rebuild from disk.

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/run_agent.py")
SENTINEL = "_is_cached_prompt_stale_for_session"


HELPER_METHODS = '''
    def _prompt_cache_marker_path(self):
        """Sentinel file for this session whose mtime represents 'when the
        cached system_prompt was last built from disk'."""
        try:
            from hermes_constants import get_hermes_home
            base = get_hermes_home() / "_prompt_cache"
        except Exception:
            return None
        try:
            base.mkdir(parents=True, exist_ok=True)
        except Exception:
            return None
        sid = (self.session_id or "default").replace("/", "_")
        return base / f"{sid}.built"

    def _record_prompt_build(self):
        """Touch the sentinel — call after a fresh _build_system_prompt + DB
        write, so we know future cache hits are valid for the current
        memory/config snapshot."""
        marker = self._prompt_cache_marker_path()
        if marker is None:
            return
        try:
            marker.touch()
        except Exception:
            pass

    def _memory_source_files(self):
        """Files whose changes should invalidate the cached system_prompt."""
        paths = []
        try:
            from tools.memory_tool import get_memory_dir
            mem_dir = get_memory_dir()
            paths.append(mem_dir / "MEMORY.md")
            paths.append(mem_dir / "USER.md")
        except Exception:
            pass
        try:
            from hermes_constants import get_config_path
            paths.append(get_config_path())
        except Exception:
            pass
        return paths

    def _is_cached_prompt_stale_for_session(self):
        """True iff any memory source file has been modified after the
        cache was last built for this session."""
        marker = self._prompt_cache_marker_path()
        if marker is None:
            return False  # can't tell — preserve current behavior
        try:
            built_at = marker.stat().st_mtime
        except OSError:
            return True  # no sentinel yet → treat as stale so first build records one
        latest = 0.0
        for p in self._memory_source_files():
            try:
                latest = max(latest, p.stat().st_mtime)
            except (OSError, AttributeError):
                pass
        return latest > built_at

'''


# Replace the stored_prompt reuse block to add the staleness check.
OLD_BLOCK = (
    '            if stored_prompt:\n'
    '                # Continuing session — reuse the exact system prompt from\n'
    '                # the previous turn so the Anthropic cache prefix matches.\n'
    '                self._cached_system_prompt = stored_prompt\n'
    '                # breakdown: keep _prompt_segments fresh on restored sessions\n'
)
NEW_BLOCK = (
    '            # If memory or config files have changed since we last built\n'
    '            # this session\'s system_prompt, drop the stale cache so the\n'
    '            # rebuild path runs and picks up the new content.\n'
    '            if stored_prompt and self._is_cached_prompt_stale_for_session():\n'
    '                logger.info(\n'
    '                    "Memory sources updated since cached system_prompt was built; rebuilding"\n'
    '                )\n'
    '                stored_prompt = None\n'
    '\n'
    '            if stored_prompt:\n'
    '                # Continuing session — reuse the exact system prompt from\n'
    '                # the previous turn so the Anthropic cache prefix matches.\n'
    '                self._cached_system_prompt = stored_prompt\n'
    '                # breakdown: keep _prompt_segments fresh on restored sessions\n'
)


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("[skip] already patched")
        return 0

    # 1) Insert helper methods near the existing compute_prompt_breakdown method
    helper_anchor = "    def compute_prompt_breakdown(\n"
    if helper_anchor not in text:
        print("FATAL: anchor for helper insertion not found", file=sys.stderr)
        return 2
    text = text.replace(helper_anchor, HELPER_METHODS + helper_anchor, 1)

    # 2) Wrap stored_prompt with the staleness check
    if OLD_BLOCK not in text:
        print("FATAL: stored_prompt anchor not found", file=sys.stderr)
        return 2
    text = text.replace(OLD_BLOCK, NEW_BLOCK)

    # 3) Touch the sentinel after each successful DB write of system_prompt
    write_old = '                        self._session_db.update_system_prompt(self.session_id, self._cached_system_prompt)\n'
    write_new = (
        '                        self._session_db.update_system_prompt(self.session_id, self._cached_system_prompt)\n'
        '                        self._record_prompt_build()\n'
    )
    if write_old in text:
        text = text.replace(write_old, write_new)
        print("  sentinel touch wired into update_system_prompt")
    else:
        print("WARN: update_system_prompt anchor not found — staleness check still works on first miss", file=sys.stderr)

    bak = P.with_suffix(P.suffix + ".cacheinval.bak")
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
