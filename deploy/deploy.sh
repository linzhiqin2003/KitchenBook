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
git pull origin main

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

echo -e "${YELLOW}🔄 7. 重启服务...${NC}"
sudo systemctl restart gunicorn
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

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx 运行正常${NC}"
else
    echo -e "${RED}✗ Nginx 启动失败${NC}"
    sudo systemctl status nginx
    exit 1
fi

echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "访问您的网站: ${GREEN}https://$(hostname -I | awk '{print $1}')${NC}"

