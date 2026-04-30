"""Vision auto-detect should follow the session's actual main model.

Bug: when a user picks a per-session model (e.g. xiaomi/mimo-v2.5 via
the patch14 model-override path), Hermes' vision_analyze tool still
reads config.yaml's default ``model.provider`` / ``model.default``
when deciding where to send images. On a host whose default is
deepseek-v4-flash that means a multimodal request gets routed to a
text-only endpoint, which serde-rejects with::

    400 - "unknown variant `image_url`, expected `text`"

…even though the user is paying for a perfectly multimodal model
(mimo-v2.5 IS native omnimodal).

Fix: introduce two ContextVars in auxiliary_client.py that the gateway
populates with the agent's actual provider+model right before each
turn runs. ``_read_main_provider()`` and ``_read_main_model()`` consult
those vars first (when set) and fall back to config.yaml otherwise, so
every code path that depends on "main provider/model" sees the
session-current values, not the gateway-default ones.

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

AUX = Path("/home/admin/.hermes/hermes-agent/agent/auxiliary_client.py")
APIS = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "# [patch15] runtime main provider/model"


# ── auxiliary_client.py edits ─────────────────────────────────────────

AUX_CTXVAR_OLD = (
    "def _read_main_model() -> str:\n"
    '    """Read the user\'s configured main model from config.yaml.\n'
)
AUX_CTXVAR_NEW = (
    "# [patch15] runtime main provider/model — populated by the gateway\n"
    "# before each agent turn, consumed by every helper that derives a\n"
    "# vision/auxiliary route from \"main provider\".\n"
    "from contextvars import ContextVar as _PV15_CV\n"
    "_RUNTIME_MAIN_PROVIDER_CV: _PV15_CV[str] = _PV15_CV(\n"
    '    "_hermes_runtime_main_provider", default=""\n'
    ")\n"
    "_RUNTIME_MAIN_MODEL_CV: _PV15_CV[str] = _PV15_CV(\n"
    '    "_hermes_runtime_main_model", default=""\n'
    ")\n"
    "\n"
    "def set_runtime_main(provider: str = \"\", model: str = \"\") -> None:\n"
    '    """Override the \'main provider/model\' for the current async context.\n'
    "\n"
    "    Used by the gateway to thread the per-session model into auxiliary\n"
    "    helpers (vision routing in particular) without touching config.yaml.\n"
    '    """\n'
    "    _RUNTIME_MAIN_PROVIDER_CV.set((provider or \"\").strip())\n"
    "    _RUNTIME_MAIN_MODEL_CV.set((model or \"\").strip())\n"
    "\n"
    "def clear_runtime_main() -> None:\n"
    "    _RUNTIME_MAIN_PROVIDER_CV.set(\"\")\n"
    "    _RUNTIME_MAIN_MODEL_CV.set(\"\")\n"
    "\n"
    "def _read_main_model() -> str:\n"
    '    """Read the user\'s configured main model from config.yaml.\n'
)

AUX_READMODEL_OLD = (
    "def _read_main_model() -> str:\n"
    '    """Read the user\'s configured main model from config.yaml.\n'
    "\n"
    "    config.yaml model.default is the single source of truth for the active\n"
    "    model. Environment variables are no longer consulted.\n"
    '    """\n'
    "    try:\n"
    "        from hermes_cli.config import load_config\n"
    "        cfg = load_config()\n"
    "        model_cfg = cfg.get(\"model\", {})\n"
)
AUX_READMODEL_NEW = (
    "def _read_main_model() -> str:\n"
    '    """Read the user\'s configured main model from config.yaml.\n'
    "\n"
    "    [patch15] Per-session override via _RUNTIME_MAIN_MODEL_CV wins over\n"
    "    config.yaml so vision and other helpers follow the active model.\n"
    "    config.yaml model.default is the fallback.\n"
    '    """\n'
    "    _runtime = _RUNTIME_MAIN_MODEL_CV.get()\n"
    "    if _runtime:\n"
    "        return _runtime\n"
    "    try:\n"
    "        from hermes_cli.config import load_config\n"
    "        cfg = load_config()\n"
    "        model_cfg = cfg.get(\"model\", {})\n"
)

AUX_READPROV_OLD = (
    "def _read_main_provider() -> str:\n"
    '    """Read the user\'s configured main provider from config.yaml.\n'
    "\n"
    "    Returns the lowercase provider id (e.g. \"alibaba\", \"openrouter\") or \"\"\n"
    "    if not configured.\n"
    '    """\n'
    "    try:\n"
    "        from hermes_cli.config import load_config\n"
    "        cfg = load_config()\n"
    "        model_cfg = cfg.get(\"model\", {})\n"
    "        if isinstance(model_cfg, dict):\n"
    "            provider = model_cfg.get(\"provider\", \"\")\n"
)
AUX_READPROV_NEW = (
    "def _read_main_provider() -> str:\n"
    '    """Read the user\'s configured main provider from config.yaml.\n'
    "\n"
    "    [patch15] Per-session override via _RUNTIME_MAIN_PROVIDER_CV wins\n"
    "    over config.yaml; falls back to config.yaml model.provider.\n"
    "    Returns the lowercase provider id (e.g. \"alibaba\", \"openrouter\") or \"\"\n"
    "    if not configured.\n"
    '    """\n'
    "    _runtime = _RUNTIME_MAIN_PROVIDER_CV.get()\n"
    "    if _runtime:\n"
    "        return _runtime.lower()\n"
    "    try:\n"
    "        from hermes_cli.config import load_config\n"
    "        cfg = load_config()\n"
    "        model_cfg = cfg.get(\"model\", {})\n"
    "        if isinstance(model_cfg, dict):\n"
    "            provider = model_cfg.get(\"provider\", \"\")\n"
)


# ── api_server.py edits ───────────────────────────────────────────────

# After agent is created (line ~2951), set runtime main from agent attrs
# right before run_conversation. The ContextVar set in this thread/coro
# context propagates to all downstream auxiliary calls (vision_analyze
# included).

APIS_OLD = (
    "            if agent_ref is not None:\n"
    "                agent_ref[0] = agent\n"
    "            result = agent.run_conversation(\n"
)
APIS_NEW = (
    "            if agent_ref is not None:\n"
    "                agent_ref[0] = agent\n"
    "            # [patch15] tell auxiliary helpers (vision in particular)\n"
    "            # the agent's actual provider/model so they don't fall back\n"
    "            # to config.yaml's gateway-default model when routing.\n"
    "            try:\n"
    "                from agent.auxiliary_client import set_runtime_main as _p15_set_runtime\n"
    "                _p15_set_runtime(\n"
    "                    getattr(agent, \"provider\", \"\") or \"\",\n"
    "                    getattr(agent, \"model\", \"\") or \"\",\n"
    "                )\n"
    "            except Exception:\n"
    "                pass\n"
    "            result = agent.run_conversation(\n"
)


def apply(path, anchors):
    text = path.read_text()
    bak = path.with_suffix(path.suffix + ".p15.bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"  backup -> {bak.name}")
    for old, new, label in anchors:
        if new in text:
            print(f"  [skip] {label} already patched")
            continue
        if old not in text:
            print(f"FATAL: anchor missing for {label}", file=sys.stderr)
            return False
        if text.count(old) != 1:
            print(f"FATAL: anchor for {label} matched {text.count(old)} times", file=sys.stderr)
            return False
        text = text.replace(old, new, 1)
        print(f"  [done] {label}")
    path.write_text(text)
    import ast
    try:
        ast.parse(path.read_text(), str(path))
        print(f"  AST ok ({path.name})")
    except SyntaxError as e:
        print(f"AST FAIL: {e}", file=sys.stderr)
        shutil.copy2(bak, path)
        return False
    return True


def main() -> int:
    aux_text = AUX.read_text()
    apis_text = APIS.read_text()
    if SENTINEL in aux_text and SENTINEL in apis_text:
        print("  [skip] already patched")
        return 0

    ok = True
    if SENTINEL not in aux_text:
        ok = apply(AUX, [
            (AUX_CTXVAR_OLD, AUX_CTXVAR_NEW, "auxiliary_client: ContextVar setup"),
            (AUX_READMODEL_OLD, AUX_READMODEL_NEW, "auxiliary_client: _read_main_model"),
            (AUX_READPROV_OLD, AUX_READPROV_NEW, "auxiliary_client: _read_main_provider"),
        ]) and ok
    if SENTINEL not in apis_text:
        # APIS_NEW carries its own marker via the [patch15] comment in the body
        # so the SENTINEL string ends up in apis_text after a successful apply.
        ok = apply(APIS, [
            (APIS_OLD, APIS_NEW, "api_server: set_runtime_main before run"),
        ]) and ok
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
