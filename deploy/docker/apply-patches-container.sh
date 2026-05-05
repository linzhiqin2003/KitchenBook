#!/bin/bash
# 容器版 apply.sh —— build 时跑，处理两件 host 版做不了的事：
#   1. 把 patches 里硬编码的 host 路径 (/home/admin/.hermes/hermes-agent, venv/) 改成
#      容器内路径 (/opt/hermes, .venv/)，再 apply
#   2. 不调用 systemctl / pip install / restart —— 容器 build 阶段没有 systemd，
#      tiktoken 由 Dockerfile 通过 uv pip 单独装
#
# 用法：apply-patches-container.sh <SRC_DIR> <PATCH_DIR>
#   SRC_DIR   : 目标 hermes 源码（默认 /src）
#   PATCH_DIR : 我们的 patches 目录（默认 /patches）

set -euo pipefail

SRC_DIR="${1:-/src}"
PATCH_DIR="${2:-/patches}"

echo "[container-patch] target src : $SRC_DIR"
echo "[container-patch] patch dir  : $PATCH_DIR"

if [ ! -d "$SRC_DIR" ]; then
    echo "ERROR: src dir not found: $SRC_DIR" >&2
    exit 1
fi
if [ ! -d "$PATCH_DIR" ]; then
    echo "ERROR: patch dir not found: $PATCH_DIR" >&2
    exit 1
fi

# 把 patches 拷到临时目录做 sed —— 不污染 host bind mount 的源
WORK="$(mktemp -d)"
cp -a "$PATCH_DIR"/*.py "$WORK/"

# 路径替换：
#   /home/admin/.hermes/hermes-agent  →  /opt/hermes (变量 SRC_DIR)
#   venv/bin                          →  .venv/bin   (上游容器用 .venv)
#
# 用 # 作分隔避免和路径里的 / 冲突
sed -i \
    -e "s#/home/admin/\.hermes/hermes-agent#${SRC_DIR}#g" \
    -e 's#\bvenv/bin#.venv/bin#g' \
    "$WORK"/*.py

# Step 1: prompt_breakdown 模块直接拷
if [ -f "$WORK/prompt_breakdown.py" ]; then
    install -m 644 "$WORK/prompt_breakdown.py" "$SRC_DIR/agent/prompt_breakdown.py"
    echo "  [done] sync agent/prompt_breakdown.py"
fi

# Step 2: 跑所有编号 patch（idempotent，按文件名排序）
shopt -s nullglob
PATCHED_COUNT=0
for script in "$WORK"/[0-9]*.py; do
    name="$(basename "$script")"
    echo "  [apply] $name"
    out="$(python3 "$script" 2>&1)" || {
        echo "PATCH FAILED: $name" >&2
        echo "$out" >&2
        exit 1
    }
    echo "$out" | sed 's/^/    /'
    PATCHED_COUNT=$((PATCHED_COUNT + 1))
done

echo "[container-patch] applied $PATCHED_COUNT numbered patches"

# Step 3: 给 cli-config.yaml.example 模板预设 approvals.mode=off
# (容器无人值守，agent 触发的 shell 命令不能等人手动 approve)
TEMPLATE="$SRC_DIR/cli-config.yaml.example"
if [ -f "$TEMPLATE" ]; then
    python3 - "$TEMPLATE" <<'PY'
import sys, yaml
from pathlib import Path
p = Path(sys.argv[1])
cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
appr = cfg.setdefault("approvals", {})
if appr.get("mode") != "off":
    appr["mode"] = "off"
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"  [done] approvals.mode=off baked into {p.name}")
else:
    print(f"  [skip] approvals.mode already off in {p.name}")
PY
fi

echo "[container-patch] done"
