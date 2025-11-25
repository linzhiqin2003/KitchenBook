# 🔄 生产环境更新指南

本次更新修复了生产环境中API请求失败的问题。

## 📋 更新内容

- ✅ 修复生产环境中 "保存失败: Network Error" 问题
- ✅ 创建统一的API配置管理
- ✅ 自动适配开发/生产环境
- ✅ 优化前端构建配置

## 🚀 在服务器上更新

### 方法一：使用自动部署脚本（推荐）

SSH连接到服务器后执行：

```bash
cd ~/KitchenBook
./deploy/deploy.sh
```

### 方法二：手动更新

```bash
# 1. SSH 连接到服务器
ssh kitchenbook@your_server_ip

# 2. 进入项目目录
cd ~/KitchenBook

# 3. 拉取最新代码
git pull origin main

# 4. 激活虚拟环境
source venv/bin/activate

# 5. 安装/更新后端依赖
cd backend
pip install -r requirements.txt

# 6. 运行数据库迁移（如果有）
python manage.py migrate

# 7. 收集静态文件
python manage.py collectstatic --noinput

# 8. 构建前端
cd ~/KitchenBook/frontend
npm install
npm run build

# 9. 重启服务
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# 10. 检查服务状态
sudo systemctl status gunicorn
sudo systemctl status nginx
```

## ✅ 验证更新

更新完成后，测试以下功能：

1. **新增菜谱**：访问 `http://your_server_ip/chef/recipes/new`
   - 填写菜品信息
   - 点击"保存更改"
   - ✅ 应该成功保存并跳转到菜谱列表

2. **编辑菜谱**：在菜谱列表点击"编辑"
   - 修改信息
   - 点击"保存更改"
   - ✅ 应该成功保存

3. **库存管理**：访问 `http://your_server_ip/chef/inventory`
   - 切换食材状态
   - 刷新页面
   - ✅ 状态应该保持

4. **订单管理**：访问 `http://your_server_ip/chef/orders`
   - 更改订单状态
   - ✅ 应该成功更新

## 🐛 如果还有问题

### 1. 检查 Nginx 日志

```bash
sudo tail -f /var/log/nginx/error.log
```

### 2. 检查 Gunicorn 日志

```bash
sudo journalctl -u gunicorn -f
```

### 3. 清除浏览器缓存

- 按 `Ctrl + Shift + R` (Windows/Linux)
- 按 `Cmd + Shift + R` (Mac)
- 或者在浏览器中强制刷新

### 4. 确认前端构建文件已更新

```bash
ls -lh ~/KitchenBook/frontend/dist/
```

应该看到新的构建时间戳。

### 5. 确认 Nginx 配置正确

```bash
sudo nginx -t
```

应该显示 "syntax is ok" 和 "test is successful"。

## 📞 常见问题

**Q: 更新后还是显示 Network Error？**
A: 
1. 确认已重启 Gunicorn 和 Nginx
2. 清除浏览器缓存
3. 检查前端 dist 文件是否更新

**Q: 页面显示白屏？**
A:
1. 检查 Nginx 错误日志
2. 确认 dist 目录权限正确：`sudo chown -R kitchenbook:www-data ~/KitchenBook/frontend/dist/`
3. 重启 Nginx

**Q: API 请求返回 502 错误？**
A:
1. 检查 Gunicorn 是否运行：`sudo systemctl status gunicorn`
2. 检查 gunicorn.sock 文件是否存在：`ls -l ~/KitchenBook/backend/gunicorn.sock`
3. 重启 Gunicorn：`sudo systemctl restart gunicorn`

---

## 🎉 更新完成！

现在您的 KitchenBook 应该可以在生产环境中正常保存菜谱和管理数据了！

如果遇到任何问题，请查看日志文件或参考 [DEPLOYMENT.md](DEPLOYMENT.md) 中的故障排查章节。

