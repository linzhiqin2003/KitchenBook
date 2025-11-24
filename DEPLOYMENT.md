# KitchenBook 云服务器部署教程

本教程将指导您将 KitchenBook 部署到云服务器（如阿里云、腾讯云、AWS 等）。

## 📋 准备工作

### 1. 服务器要求
- **操作系统**: Ubuntu 20.04 LTS 或 22.04 LTS
- **配置**: 最低 2GB RAM, 2 核 CPU, 20GB 硬盘
- **网络**: 公网 IP 地址，开放 80 和 443 端口

### 2. 域名准备（可选但推荐）
- 购买域名（如 `kitchenbook.com`）
- 将域名 A 记录指向服务器公网 IP

### 3. 本地准备
- 确保本地项目代码已提交到 Git 仓库（GitHub/GitLab/Gitee）

---

## 🚀 部署步骤

### 第一步：连接服务器并更新系统

```bash
# SSH 连接服务器
ssh root@your_server_ip

# 更新系统软件包
apt update && apt upgrade -y

# 安装必要工具
apt install -y git curl vim ufw
```

### 第二步：创建部署用户

```bash
# 创建非 root 用户（安全考虑）
adduser kitchenbook
usermod -aG sudo kitchenbook

# 切换到新用户
su - kitchenbook
```

### 第三步：安装 Python 环境

```bash
# 安装 Python 3.11 和相关工具
sudo apt install -y python3.11 python3.11-venv python3-pip python3-dev

# 安装 PostgreSQL
sudo apt install -y postgresql postgresql-contrib libpq-dev

# 启动 PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 第四步：配置数据库

```bash
# 切换到 postgres 用户创建数据库
sudo -u postgres psql

# 在 psql 命令行中执行：
CREATE DATABASE kitchenbook_db;
CREATE USER kitchenbook_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE kitchenbook_user SET client_encoding TO 'utf8';
ALTER ROLE kitchenbook_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE kitchenbook_user SET timezone TO 'Asia/Shanghai';
GRANT ALL PRIVILEGES ON DATABASE kitchenbook_db TO kitchenbook_user;
\q
```

### 第五步：下载项目代码

```bash
# 回到 kitchenbook 用户主目录
cd ~

# 从 Git 仓库克隆项目（替换为您的仓库地址）
git clone https://github.com/yourusername/KitchenBook.git
cd KitchenBook

# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装后端依赖
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install gunicorn psycopg2-binary
```

### 第六步：配置 Django 生产环境

```bash
# 创建环境变量文件
nano backend/.env
```

在 `.env` 文件中添加以下内容：

```env
# Django 配置
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=your_domain.com,your_server_ip

# 数据库配置
DB_NAME=kitchenbook_db
DB_USER=kitchenbook_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432

# 其他配置
CORS_ALLOWED_ORIGINS=https://your_domain.com
```

```bash
# 生成 Django SECRET_KEY
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
# 将生成的 key 复制到上面的 SECRET_KEY
```

### 第七步：配置 Django 使用 PostgreSQL

编辑 `backend/config/settings.py`，Django 会自动读取环境变量（配置文件已在步骤八中更新）。

### 第八步：运行数据库迁移

```bash
cd ~/KitchenBook
source venv/bin/activate

# 收集静态文件
cd backend
python manage.py collectstatic --noinput

# 运行数据库迁移
python manage.py migrate

# 创建管理员账号
python manage.py createsuperuser

# 填充示例数据（可选）
python manage.py seed_data
```

### 第九步：安装和配置 Gunicorn

```bash
# 测试 Gunicorn 是否正常工作
cd ~/KitchenBook/backend
gunicorn --bind 0.0.0.0:8000 config.wsgi:application

# 如果正常，按 Ctrl+C 停止，然后创建 systemd 服务
sudo nano /etc/systemd/system/gunicorn.service
```

添加以下内容：

```ini
[Unit]
Description=Gunicorn daemon for KitchenBook
After=network.target

[Service]
User=kitchenbook
Group=www-data
WorkingDirectory=/home/kitchenbook/KitchenBook/backend
Environment="PATH=/home/kitchenbook/KitchenBook/venv/bin"
ExecStart=/home/kitchenbook/KitchenBook/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/home/kitchenbook/KitchenBook/backend/gunicorn.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# 启动 Gunicorn 服务
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# 检查状态
sudo systemctl status gunicorn
```

### 第十步：安装 Node.js 和构建前端

```bash
# 安装 Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 构建前端
cd ~/KitchenBook/frontend
npm install
npm run build

# 构建完成后，dist 目录包含静态文件
```

### 第十一步：安装和配置 Nginx

```bash
# 安装 Nginx
sudo apt install -y nginx

# 创建 Nginx 配置文件
sudo nano /etc/nginx/sites-available/kitchenbook
```

添加以下内容：

```nginx
server {
    listen 80;
    server_name your_domain.com your_server_ip;
    client_max_body_size 10M;

    # 前端静态文件
    location / {
        root /home/kitchenbook/KitchenBook/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Django 静态文件
    location /static/ {
        alias /home/kitchenbook/KitchenBook/backend/staticfiles/;
    }

    # Django 媒体文件
    location /media/ {
        alias /home/kitchenbook/KitchenBook/backend/media/;
    }

    # Django API
    location /api/ {
        proxy_pass http://unix:/home/kitchenbook/KitchenBook/backend/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://unix:/home/kitchenbook/KitchenBook/backend/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 创建符号链接启用站点
sudo ln -s /etc/nginx/sites-available/kitchenbook /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试 Nginx 配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 第十二步：配置防火墙

```bash
# 允许 SSH、HTTP 和 HTTPS
sudo ufw allow 'OpenSSH'
sudo ufw allow 'Nginx Full'

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

### 第十三步：配置 HTTPS（推荐，使用 Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取 SSL 证书（替换为您的域名和邮箱）
sudo certbot --nginx -d your_domain.com -d www.your_domain.com --email your_email@example.com --agree-tos --no-eff-email

# 测试自动续期
sudo certbot renew --dry-run
```

---

## ✅ 验证部署

1. **访问网站**: 在浏览器打开 `http://your_domain.com` 或 `http://your_server_ip`
2. **测试前端**: 确认首页能正常显示菜谱列表
3. **测试 API**: 访问 `http://your_domain.com/api/recipes/`
4. **测试后台**: 访问 `http://your_domain.com/admin` 并登录

---

## 🔄 日常维护命令

### 更新代码

```bash
cd ~/KitchenBook
git pull origin main
source venv/bin/activate

# 更新后端
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn

# 更新前端
cd ~/KitchenBook/frontend
npm install
npm run build

# 重启 Nginx
sudo systemctl restart nginx
```

### 查看日志

```bash
# Gunicorn 日志
sudo journalctl -u gunicorn -f

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# Django 日志（如果配置了文件日志）
tail -f ~/KitchenBook/backend/logs/django.log
```

### 备份数据库

```bash
# 创建备份目录
mkdir -p ~/backups

# 备份数据库
sudo -u postgres pg_dump kitchenbook_db > ~/backups/kitchenbook_$(date +%Y%m%d_%H%M%S).sql

# 备份媒体文件
tar -czf ~/backups/media_$(date +%Y%m%d_%H%M%S).tar.gz ~/KitchenBook/backend/media/
```

### 恢复数据库

```bash
# 从备份恢复
sudo -u postgres psql kitchenbook_db < ~/backups/kitchenbook_20250124_120000.sql
```

---

## 🐛 故障排查

### 问题 1: 静态文件不显示

```bash
# 检查静态文件是否收集
cd ~/KitchenBook/backend
python manage.py collectstatic --noinput

# 检查文件权限
sudo chown -R kitchenbook:www-data ~/KitchenBook/backend/staticfiles/
sudo chmod -R 755 ~/KitchenBook/backend/staticfiles/
```

### 问题 2: Gunicorn 无法启动

```bash
# 查看详细错误
sudo journalctl -u gunicorn -n 50

# 检查 socket 文件权限
ls -l ~/KitchenBook/backend/gunicorn.sock
```

### 问题 3: 502 Bad Gateway

```bash
# 检查 Gunicorn 是否运行
sudo systemctl status gunicorn

# 检查 socket 文件是否存在
ls -l ~/KitchenBook/backend/gunicorn.sock

# 重启服务
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### 问题 4: 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 测试数据库连接
cd ~/KitchenBook/backend
source ../venv/bin/activate
python manage.py dbshell
```

---

## 🔐 安全建议

1. **定期更新系统**: `sudo apt update && sudo apt upgrade`
2. **使用强密码**: 数据库、Django admin、服务器登录
3. **限制 SSH**: 禁用 root 登录，使用密钥认证
4. **配置防火墙**: 只开放必要端口
5. **定期备份**: 数据库和媒体文件
6. **监控日志**: 定期查看异常访问
7. **使用 HTTPS**: 保护用户数据传输

---

## 📱 性能优化建议

1. **启用 Nginx 缓存**
2. **配置 Redis 缓存**（Django 缓存后端）
3. **使用 CDN 加速静态资源**
4. **优化数据库查询**
5. **增加 Gunicorn workers 数量**（根据 CPU 核心数）

---

## 📞 需要帮助？

如果部署过程中遇到问题：
1. 检查日志文件（Gunicorn、Nginx、Django）
2. 确认防火墙和端口设置
3. 验证文件权限
4. 参考故障排查章节

祝您部署顺利！🎉

