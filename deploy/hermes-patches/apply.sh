#!/bin/bash
# Apply local Hermes patches that are not yet upstream.
# Idempotent: each Python patch script detects already-applied state
# and skips. Safe to run on every deploy.
#
# What gets applied:
#   - agent/prompt_breakdown.py        — new module, copied if missing/changed
#   - 01_breakdown_wiring.py           — _build_system_prompt + result dict + api_server usage
#   - 02_segments_refresh.py           — refresh _prompt_segments on session restore
#   - 03_tools_handler_fix.py          — switch /api/tools to _get_effective_configurable_toolsets
#
# Restarts hermes-gateway.service only when something actually changed.

set -e

HERMES="/home/admin/.hermes/hermes-agent"
SRC="$(cd "$(dirname "$0")" && pwd)"
PY="$HERMES/venv/bin/python3"
GATEWAY_UNIT="hermes-gateway.service"

if [ ! -d "$HERMES" ]; then
  echo "  [skip] Hermes not installed at $HERMES — nothing to patch."
  exit 0
fi
if [ ! -x "$PY" ]; then
  echo "  [skip] Hermes venv missing at $PY — nothing to patch."
  exit 0
fi

CHANGED=0

# 1) Drop in the prompt_breakdown module — copy only if missing or differs
DEST="$HERMES/agent/prompt_breakdown.py"
if ! cmp -s "$SRC/prompt_breakdown.py" "$DEST" 2>/dev/null; then
  cp "$SRC/prompt_breakdown.py" "$DEST"
  echo "  [done] sync agent/prompt_breakdown.py"
  CHANGED=1
else
  echo "  [skip] agent/prompt_breakdown.py up to date"
fi

# 2) Ensure tiktoken is installed in Hermes venv (precise tokenizer)
if ! "$PY" -c "import tiktoken" 2>/dev/null; then
  echo "  [done] installing tiktoken into Hermes venv"
  "$HERMES/venv/bin/pip" install --quiet 'tiktoken>=0.7.0,<1'
  CHANGED=1
else
  echo "  [skip] tiktoken already installed"
fi

# 3) Run each numbered patch script — they're all idempotent
for script in "$SRC"/[0-9]*.py; do
  out=$("$PY" "$script")
  echo "$out" | sed 's/^/  /'
  # "已应用" 状态用 [skip] / "already patched" 表示。只有真正 patch 当下才算 CHANGED。
  # 之前的 grep -q "patched" 误判 — "already patched" 也含 "patched"，导致每次都触发重启。
  if echo "$out" | grep -q "patched" && ! echo "$out" | grep -qE "already patched|\[skip\]"; then
    CHANGED=1
  fi
done

# 4) Ensure approval prompts are off in the gateway — there's no human at a
#    terminal to click "approve", so the agent's tirith security scan would
#    otherwise leave every flagged shell command pending forever.  Idempotent.
"$PY" - <<'PY_END'
from pathlib import Path
import yaml
targets = [Path.home() / ".hermes" / "config.yaml"]
users_dir = Path.home() / ".hermes" / "users"
if users_dir.is_dir():
    for d in users_dir.iterdir():
        cfg = d / "config.yaml"
        if cfg.is_file():
            targets.append(cfg)
for p in targets:
    try:
        cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        cfg = {}
    if not isinstance(cfg, dict):
        continue
    appr = cfg.setdefault("approvals", {})
    if appr.get("mode") == "off":
        continue
    appr["mode"] = "off"
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"  [done] approvals.mode=off in {p}")
PY_END

# 5) Restart only when something actually changed
#    部署模式有两种：
#      A. user systemd unit (hermes-gateway.service) — 直接跑 venv
#      B. system docker (hermes-docker.service)      — 容器化（当前生产）
#    不同模式 patch 路径也不一样：A 修 host 文件就生效；B 修了 host 但容器
#    内 image 不变（patches 是 build 阶段烧进 image 的）所以重启容器没意义。
#    docker 模式下我们只确认 host 文件 patch 状态，**不**尝试重启服务。
if [ "$CHANGED" -eq 1 ]; then
  # list-unit-files 即使 unit 不存在也返回 0 — 显式 grep 确认它真注册了
  if systemctl --user list-unit-files --no-legend 2>/dev/null | grep -q "^$GATEWAY_UNIT"; then
    if systemctl --user restart "$GATEWAY_UNIT" 2>/dev/null; then
      sleep 2
      state=$(systemctl --user is-active "$GATEWAY_UNIT" || true)
      echo "  hermes-gateway: $state"
    else
      echo "  [warn] hermes-gateway restart failed — continuing"
    fi
  else
    echo "  [skip] no user hermes-gateway.service — assume docker mode (rebuild image to apply patches)"
  fi
else
  echo "  [skip] no Hermes changes — gateway restart not needed"
fi
