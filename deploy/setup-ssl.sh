#!/bin/bash

# KitchenBook SSL 证书配置脚本
# 使用 Let's Encrypt 免费 SSL 证书
# 使用方法: sudo ./setup-ssl.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN="lzqqqkitchen.org"
EMAIL="your-email@example.com"  # 请修改为你的邮箱

echo -e "${BLUE}🔐 KitchenBook SSL 证书配置${NC}"
echo -e "${YELLOW}域名: ${DOMAIN}${NC}"
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 步骤 1: 安装 Certbot
echo -e "${YELLOW}📦 1. 安装 Certbot...${NC}"
if ! command -v certbot &> /dev/null; then
    apt update
    apt install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✓ Certbot 安装完成${NC}"
else
    echo -e "${GREEN}✓ Certbot 已安装${NC}"
fi

# 步骤 2: 创建验证目录
echo -e "${YELLOW}📁 2. 创建验证目录...${NC}"
mkdir -p /var/www/certbot
chown -R www-data:www-data /var/www/certbot
echo -e "${GREEN}✓ 验证目录已创建${NC}"

# 步骤 3: 临时 Nginx 配置（用于获取证书）
echo -e "${YELLOW}⚙️  3. 配置临时 Nginx（用于验证）...${NC}"

# 备份当前配置
if [ -f /etc/nginx/sites-enabled/kitchenbook ]; then
    cp /etc/nginx/sites-enabled/kitchenbook /etc/nginx/sites-enabled/kitchenbook.backup
fi

# 创建临时配置（只用于验证）
cat > /etc/nginx/sites-enabled/kitchenbook << 'EOF'
server {
    listen 80;
    server_name lzqqqkitchen.org www.lzqqqkitchen.org;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        root /home/kitchenbook/KitchenBook/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
EOF

# 重载 Nginx
nginx -t && systemctl reload nginx
echo -e "${GREEN}✓ 临时配置已应用${NC}"

# 步骤 4: 获取 SSL 证书
echo -e "${YELLOW}🔑 4. 获取 SSL 证书...${NC}"
echo -e "${BLUE}   这可能需要几秒钟...${NC}"

certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d ${DOMAIN} \
    -d www.${DOMAIN} \
    --non-interactive \
    --agree-tos \
    --email ${EMAIL} \
    || {
        echo -e "${RED}❌ 证书获取失败！${NC}"
        echo -e "${YELLOW}可能的原因：${NC}"
        echo "1. 域名 DNS 未正确指向此服务器"
        echo "2. 防火墙阻止了 80 端口"
        echo "3. 邮箱地址无效"
        echo ""
        echo "请检查后重试，或手动运行："
        echo "  sudo certbot certonly --nginx -d ${DOMAIN} -d www.${DOMAIN}"
        exit 1
    }

echo -e "${GREEN}✓ SSL 证书获取成功！${NC}"

# 步骤 5: 应用完整的 HTTPS 配置
echo -e "${YELLOW}⚙️  5. 应用 HTTPS 配置...${NC}"
cp /home/kitchenbook/KitchenBook/deploy/nginx.conf /etc/nginx/sites-enabled/kitchenbook

# 测试配置
nginx -t || {
    echo -e "${RED}❌ Nginx 配置错误！${NC}"
    # 恢复备份
    if [ -f /etc/nginx/sites-enabled/kitchenbook.backup ]; then
        mv /etc/nginx/sites-enabled/kitchenbook.backup /etc/nginx/sites-enabled/kitchenbook
    fi
    exit 1
}

# 重载 Nginx
systemctl reload nginx
echo -e "${GREEN}✓ HTTPS 配置已应用${NC}"

# 步骤 6: 设置自动续期
echo -e "${YELLOW}🔄 6. 配置证书自动续期...${NC}"

# 测试续期
certbot renew --dry-run || echo -e "${YELLOW}⚠️ 续期测试失败，请手动检查${NC}"

# 添加 cron 任务（每天凌晨 3 点检查续期）
(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
echo -e "${GREEN}✓ 自动续期已配置${NC}"

# 清理
rm -f /etc/nginx/sites-enabled/kitchenbook.backup

echo ""
echo -e "${GREEN}🎉 SSL 配置完成！${NC}"
echo ""
echo -e "证书位置: /etc/letsencrypt/live/${DOMAIN}/"
echo -e "证书有效期: 90 天（自动续期）"
echo ""
echo -e "${GREEN}现在可以通过 HTTPS 访问你的网站了：${NC}"
echo -e "  ${BLUE}https://${DOMAIN}${NC}"
echo ""

