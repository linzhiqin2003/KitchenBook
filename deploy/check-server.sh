#!/bin/bash

# KitchenBook 服务器环境检查脚本

echo "🔍 KitchenBook 服务器环境检查"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装: $(command -v $1)"
        if [ "$1" = "python3" ]; then
            echo "  版本: $(python3 --version)"
        elif [ "$1" = "node" ]; then
            echo "  版本: $(node --version)"
        elif [ "$1" = "psql" ]; then
            echo "  版本: $(psql --version)"
        fi
    else
        echo -e "${RED}✗${NC} $1 未安装"
        return 1
    fi
}

check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "${GREEN}✓${NC} $1 服务运行中"
    else
        echo -e "${RED}✗${NC} $1 服务未运行"
        return 1
    fi
}

check_port() {
    if netstat -tuln | grep -q ":$1 "; then
        echo -e "${GREEN}✓${NC} 端口 $1 已开放"
    else
        echo -e "${YELLOW}!${NC} 端口 $1 未监听"
    fi
}

echo "📦 1. 检查必要软件"
echo "-------------------"
check_command python3
check_command pip3
check_command node
check_command npm
check_command psql
check_command nginx
check_command git
echo ""

echo "🚀 2. 检查服务状态"
echo "-------------------"
check_service postgresql
check_service nginx
if systemctl list-units --type=service | grep -q gunicorn; then
    check_service gunicorn
else
    echo -e "${YELLOW}!${NC} gunicorn 服务未配置"
fi
echo ""

echo "🌐 3. 检查网络端口"
echo "-------------------"
check_port 80
check_port 443
check_port 5432
echo ""

echo "💾 4. 检查磁盘空间"
echo "-------------------"
df -h / | awk 'NR==1{print $0} NR==2{printf "使用: %s / %s (%s)\n", $3, $2, $5}'
echo ""

echo "🧠 5. 检查内存使用"
echo "-------------------"
free -h | awk 'NR==2{printf "内存: %s / %s (%.0f%%)\n", $3, $2, $3/$2 * 100}'
echo ""

echo "🔒 6. 检查防火墙状态"
echo "-------------------"
if command -v ufw &> /dev/null; then
    sudo ufw status | head -5
else
    echo -e "${YELLOW}!${NC} ufw 未安装"
fi
echo ""

echo "📁 7. 检查项目目录"
echo "-------------------"
if [ -d ~/KitchenBook ]; then
    echo -e "${GREEN}✓${NC} 项目目录存在: ~/KitchenBook"
    if [ -d ~/KitchenBook/venv ]; then
        echo -e "${GREEN}✓${NC} Python 虚拟环境已创建"
    else
        echo -e "${RED}✗${NC} Python 虚拟环境未创建"
    fi
    if [ -f ~/KitchenBook/backend/.env ]; then
        echo -e "${GREEN}✓${NC} 环境变量文件已配置"
    else
        echo -e "${RED}✗${NC} 环境变量文件未配置"
    fi
else
    echo -e "${RED}✗${NC} 项目目录不存在"
fi
echo ""

echo "================================"
echo "检查完成！"

