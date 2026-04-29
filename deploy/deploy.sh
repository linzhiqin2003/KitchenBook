#!/bin/bash

# KitchenBook 一键部署脚本
# 使用方法: ./deploy.sh

set -e  # 遇到错误立即退出

echo "🚀 开始部署 KitchenBook..."

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 进入项目目录
cd ~/KitchenBook

echo -e "${YELLOW}📦 1. 拉取最新代码...${NC}"
# 服务器上的 working tree 可能因为热补丁（直接 scp / sed）而处于 dirty 状态。
# 这种"本地改动"通常是上一次还没 commit 的紧急修复，commit 已经 push 上来后
# 用 git pull 会撞 "would be overwritten by merge" 报错并 abort 整个 deploy。
# 这里先把 dirty 都 stash（含 untracked），pull 完再尝试 pop —— 如果 pop 冲突
# （说明 stash 的内容已经被 origin 里的 commit 覆盖），就丢弃 stash，原 working
# tree 已经被 origin 的版本替代，正是想要的结果。
AUTOSTASHED=0
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo -e "${YELLOW}⚠️  working tree 有未提交改动，先 stash 让 pull 能跑${NC}"
    git stash push -u -m "deploy.sh autostash $(date -u +%FT%TZ)" || true
    AUTOSTASHED=1
fi
git pull --rebase=false origin main
if [ "$AUTOSTASHED" = "1" ]; then
    if git stash pop 2>/dev/null; then
        echo -e "${YELLOW}↻ stash 已恢复（pull 不冲突）${NC}"
    else
        echo -e "${YELLOW}↻ stash 恢复冲突 → 已被 origin/main 取代，丢弃 stash${NC}"
        # pop 留下的冲突标记需要 reset 干净
        git checkout -- . 2>/dev/null || true
        git stash drop 2>/dev/null || true
    fi
fi

echo -e "${YELLOW}🐍 2. 激活虚拟环境...${NC}"
source venv/bin/activate

echo -e "${YELLOW}📚 3. 安装后端依赖...${NC}"
cd backend
pip install -q -r requirements.txt

echo -e "${YELLOW}🗄️  4. 运行数据库迁移...${NC}"
python manage.py migrate --noinput

echo -e "${YELLOW}📦 5. 收集静态文件...${NC}"
python manage.py collectstatic --noinput

echo -e "${YELLOW}🎨 6. 构建前端...${NC}"
cd ~/KitchenBook/frontend
npm install --silent
npm run build

echo -e "${YELLOW}🧾 6.1 构建 Receipts 前端...${NC}"
cd ~/KitchenBook/receipts-frontend
npm install --silent
npm run build

echo -e "${YELLOW}🧠 6.2 同步 Hermes 本地补丁...${NC}"
bash ~/KitchenBook/deploy/hermes-patches/apply.sh

echo -e "${YELLOW}🔄 7. 重启服务...${NC}"
sudo systemctl restart gunicorn
sudo systemctl restart daphne
sleep 2
sudo systemctl restart nginx

echo -e "${YELLOW}✅ 8. 检查服务状态...${NC}"
if systemctl is-active --quiet gunicorn; then
    echo -e "${GREEN}✓ Gunicorn 运行正常${NC}"
else
    echo -e "${RED}✗ Gunicorn 启动失败${NC}"
    sudo journalctl -u gunicorn -n 20
    exit 1
fi

if systemctl is-active --quiet daphne; then
    echo -e "${GREEN}✓ Daphne (WebSocket) 运行正常${NC}"
else
    echo -e "${RED}✗ Daphne 启动失败${NC}"
    sudo journalctl -u daphne -n 20
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx 运行正常${NC}"
else
    echo -e "${RED}✗ Nginx 启动失败${NC}"
    sudo systemctl status nginx
    exit 1
fi

echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "访问您的网站: ${GREEN}https://$(hostname -I | awk '{print $1}')${NC}"

