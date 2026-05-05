#!/bin/bash
# 把 host 上 ~/.hermes/hermes-agent (已 patched 的工作版本) snapshot 到
# deploy/docker/_hermes_source/，供 docker build 用。
#
# 为什么不在容器里 git clone + apply patches：上游 hermes 持续演化，patches
# 是基于更老的 commit 写的，部分 anchor 在新 commit 里被上游收编/重构掉了。
# host 上的 apply.sh 是 idempotent，已经把状态固化在文件里 —— 直接照搬最稳。
#
# 此脚本在哪跑：
#   - 服务器：每次容器化升级前，跑一次（host 上 git pull 上游 + apply.sh 后）
#   - Mac：开发时如果 Mac 上没装 hermes，可以 scp 服务器的 source 过来
#
# 用法：bash deploy/docker/prepare-source.sh [SOURCE_DIR]
#   SOURCE_DIR 默认 $HOME/.hermes/hermes-agent

set -euo pipefail

SOURCE_DIR="${1:-$HOME/.hermes/hermes-agent}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="$SCRIPT_DIR/_hermes_source"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "ERROR: source not found: $SOURCE_DIR" >&2
    echo "Hermes 没装在默认位置。手动指定：bash $0 /path/to/hermes-agent" >&2
    exit 1
fi

echo "[prepare-source] source: $SOURCE_DIR"
echo "[prepare-source] dest:   $DEST"

# 排除：python venv / node_modules / git 历史 / patch 备份 / 缓存 / 编辑器
# 注意：不排除 web/dist 和 ui-tui/dist —— 上游 entrypoint 不需要它们，
# 容器内 npm run build 会重建。但保留 dist 也无害，删了 build 会再 gen。
rsync -a --delete \
    --exclude='venv/' \
    --exclude='**/node_modules/' \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='*.bak' \
    --exclude='*.swp' \
    --exclude='.DS_Store' \
    --exclude='hermes_agent.egg-info/' \
    "$SOURCE_DIR/" "$DEST/"

# 大小报告
SIZE=$(du -sh "$DEST" | awk '{print $1}')
COUNT=$(find "$DEST" -type f | wc -l)
echo "[prepare-source] done — $COUNT files, $SIZE"
