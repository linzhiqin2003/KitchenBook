# ReceiptAnalysis (Django 5 + Vue 3)

本项目实现「收据拍照上传 -> 豆包 VLM 解析 -> JSON 校对 -> 入库统计」的完整链路。

## 结构
- `backend/` Django 5 + DRF
- `frontend/` Vue 3 + Vite + ECharts

## 后端启动
1. 创建虚拟环境并安装依赖
2. 配置 `.env`（参考 `backend/.env.example`）
3. 迁移数据库
4. 运行服务

示例命令：
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## 前端启动
```bash
cd frontend
npm install
npm run dev
```

默认前端访问 `http://localhost:5173`，后端 API 为 `http://localhost:8000/api`。

## 生产部署建议
- 使用 Nginx 反向代理 `/api/` 到 Django
- 前端执行 `npm run build` 生成静态文件，Nginx 直接托管
- Django 建议使用 `gunicorn` 或 `uvicorn` 托管

## 关键环境变量
后端 `.env`：
```
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
DEFAULT_CURRENCY=GBP

ARK_API_KEY=your-ark-api-key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL_ID=your-endpoint-id
```

前端 `.env`（可选）：
```
VITE_API_BASE=http://localhost:8000/api
```
