# MyWeb 项目记忆文件

> LZQ 个人综合平台，域名 www.lzqqq.org

## 技术栈

- **后端**: Django 5.2 + DRF + Daphne (WebSocket) | SQLite (开发) / PostgreSQL (生产)
- **主前端**: Vue 3 + Vite + Tailwind CSS + Vue Router + Axios
- **记账前端**: 独立 Vue 3 应用（JWT 认证）
- **部署**: Nginx + Gunicorn + Daphne + Systemd

## 项目结构

```
MyWeb/
├── backend/                 # Django 后端（统一 API 服务）
│   ├── config/              #   Django 配置 (settings.py, urls.py, asgi.py)
│   ├── api/                 #   厨房系统：菜谱/订单/博客/AI对话
│   ├── accounts/            #   用户系统：JWT 认证 + 组织管理
│   ├── receipts/            #   记账系统：收据/分类/统计
│   ├── cards/               #   塔罗牌数据
│   ├── readings/            #   塔罗牌阵
│   ├── oracle/              #   塔罗占卜
│   ├── questions/           #   AI 出题模块
│   ├── apps/
│   │   ├── interpretation/  #   同声传译：ASR + 翻译 + TTS
│   │   └── emoji_generator/ #   表情包视频生成（DashScope）
│   ├── common/              #   共享配置：多 LLM 提供商管理
│   └── media/               #   用户上传文件
├── frontend/                # 主前端（厨房/博客/AI Lab/塔罗/出题）
│   └── src/
│       ├── views/           #   页面组件
│       ├── components/      #   可复用组件（含 ailab/ tarot/ 子目录）
│       ├── api/             #   API 客户端模块
│       ├── store/           #   状态管理 (auth.js, cart.js)
│       ├── config/          #   配置文件 (api.js, aiLab.js)
│       └── router/          #   路由配置
├── receipts-frontend/       # 记账前端（独立应用，JWT 认证）
├── deploy/                  # 部署脚本与配置
└── docs/                    # 文档
```

## 后端 API 路由总览 (backend/config/urls.py)

| 路由前缀 | 应用 | 说明 |
|----------|------|------|
| `/api/` | api | 厨房：菜谱/食材/订单/博客/AI对话/会话管理 |
| `/api/questiongen/` | questions | AI 出题 |
| `/api/interpretation/` | apps.interpretation | 同声传译服务 |
| `/api/emoji/` | apps.emoji_generator | 表情包视频生成 |
| `/receipts/api/` | receipts + accounts | 记账系统 + 用户认证 |

## 前端路由模块 (frontend/src/router/index.js)

| 模块 | 路径前缀 | 说明 |
|------|---------|------|
| 首页 | `/` | 个人主页 (PortfolioHomeView) |
| 厨房 | `/kitchen/` | 菜谱浏览/点餐/厨师后台 |
| 博客 | `/blog/` | 技术博客（独立暗色主题） |
| AI Lab | `/ai-lab/` | AI 对话/翻译工作室/表情包生成 |
| 出题 | `/questiongen` | AI 出题系统 |
| 塔罗 | `/tarot/` | 塔罗占卜 |

厨师后台路由需 `meta: { requiresAuth: true, authType: 'chef' }`。

### 记账前端路由 (receipts-frontend/src/router/index.ts)

独立 Vue 应用，部署在 `/receipts/` 路径下，JWT 认证。

| 路径 | 说明 |
|------|------|
| `/` | 仪表盘统计 |
| `/upload` | 上传收据 |
| `/receipts` | 收据列表 |
| `/receipts/:id` | 收据详情 |
| `/profile` | 个人资料 |
| `/org-settings` | 组织管理 |
| `/login` | 登录 |
| `/register` | 注册 |
| `/invite/:id` | 接受邀请 |

## 认证机制

- **厨师认证**: SHA256 token，凭证在 settings.py 环境变量配置
- **记账系统认证**: JWT (rest_framework_simplejwt)，独立用户系统 + 组织管理

## 开发命令

```bash
# 后端
cd backend && source ../venv/bin/activate
python manage.py runserver          # http://127.0.0.1:8000
python manage.py makemigrations && python manage.py migrate

# 主前端
cd frontend && npm run dev          # http://localhost:5173

# 记账前端
cd receipts-frontend && npm run dev # http://localhost:5174
```

## 开发注意事项

- 修改模型后必须 `makemigrations` + `migrate`
- 新增 API 字段需同步更新 serializers.py 的 `fields`
- 前端 API 地址通过 `config/api.js` 统一管理，生产环境使用相对路径
- Vite 开发代理已配置 `/api` 和 `/media` 转发到后端
- 样式使用 Tailwind，厨房模块 emerald/amber/stone 配色，博客模块紫色暗色主题

## 服务器部署

- **域名**: www.lzqqq.org
- **连接**: `ssh myserver`
- **部署脚本**: `deploy/` 目录（deploy.sh, nginx.conf, gunicorn.service, daphne.service 等）
- **服务器上已有项目和部署脚本**，每次代码更新后需要重新部署

### 部署流程

1. 本地完成开发，构建前端：
   ```bash
   cd frontend && npm run build
   cd receipts-frontend && npm run build
   ```
2. 推送代码到远程仓库
3. SSH 到服务器执行部署脚本：
   ```bash
   ssh myserver
   cd ~/MyWeb  # 或项目实际路径
   git pull
   bash deploy/deploy.sh
   ```
