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
for script in "$SRC"/0*.py; do
  out=$("$PY" "$script")
  echo "$out" | sed 's/^/  /'
  if echo "$out" | grep -q "patched"; then
    CHANGED=1
  fi
done

# 4) Restart only when something actually changed
if [ "$CHANGED" -eq 1 ]; then
  if systemctl --user list-unit-files "$GATEWAY_UNIT" >/dev/null 2>&1; then
    systemctl --user restart "$GATEWAY_UNIT"
    sleep 2
    state=$(systemctl --user is-active "$GATEWAY_UNIT" || true)
    echo "  hermes-gateway: $state"
  fi
else
  echo "  [skip] no Hermes changes — gateway restart not needed"
fi
