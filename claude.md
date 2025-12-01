# KitchenBook 项目架构文档

> 供 AI 后续代码更新时参考的技术文档

## 📋 项目概述

**KitchenBook** 是一个现代化的在线菜谱与点餐管理系统，具有拟物化的翻书效果。系统分为**顾客端**和**厨师后台**两个部分。

### 核心功能
- 🎨 精美UI + 翻书效果 (page-flip 库)
- 🛒 顾客点餐系统
- 👨‍🍳 厨师后台管理（订单、菜谱、库存）
- ✍️ 技术博客模块
- 🤖 AI 对话助手（DeepSeek API）

---

## 🏗️ 技术栈

### 后端
- **Django 5.2** + **Django REST Framework**
- **SQLite** (开发) / **PostgreSQL** (生产)
- **Pillow** (图片处理)
- **Gunicorn** + **Nginx** (生产部署)

### 前端
- **Vue 3** + **Vite**
- **Tailwind CSS** (样式)
- **Vue Router** (路由)
- **Pinia/reactive** (状态管理 - 实际使用 Vue reactive)
- **page-flip** (翻书效果)
- **Axios** (HTTP 请求)

---

## 📁 项目结构

```
KitchenBook/
├── backend/                    # Django 后端
│   ├── api/                    # 主 API 应用
│   │   ├── models.py          # 数据模型
│   │   ├── views.py           # API 视图 (ViewSets)
│   │   ├── serializers.py     # DRF 序列化器
│   │   ├── urls.py            # API 路由
│   │   └── management/commands/seed_data.py  # 数据填充
│   ├── config/                 # Django 配置
│   │   ├── settings.py        # 主配置文件
│   │   └── urls.py            # 根路由
│   ├── media/                  # 用户上传文件
│   └── db.sqlite3             # 开发数据库
│
├── frontend/                   # Vue 前端
│   ├── src/
│   │   ├── App.vue            # 根组件 (含导航栏)
│   │   ├── main.js            # 入口文件
│   │   ├── router/index.js    # 路由配置
│   │   ├── store/             # 状态管理
│   │   │   ├── auth.js        # 厨师认证状态
│   │   │   └── cart.js        # 购物车状态
│   │   ├── config/api.js      # API 基础地址配置
│   │   ├── views/             # 页面组件
│   │   └── components/        # 可复用组件
│   ├── vite.config.js         # Vite 配置
│   └── tailwind.config.js     # Tailwind 配置
│
└── deploy/                     # 部署相关文件
```

---

## 🗄️ 数据模型 (backend/api/models.py)

### 核心模型

| 模型 | 说明 | 关键字段 |
|------|------|----------|
| `Ingredient` | 食材库存 | `name`, `quantity`, `unit`, `threshold` |
| `Recipe` | 菜谱 | `title`, `cover_image`, `description`, `cooking_time`, `category`, `is_public`, `chef_notes` |
| `RecipeIngredient` | 菜谱食材关联 | `recipe` (FK), `ingredient` (FK), `amount`, `quantity_display` |
| `RecipeStep` | 烹饪步骤 | `recipe` (FK), `step_number`, `description`, `image` |
| `Order` | 订单 | `customer_name`, `status` (pending/cooking/completed), `created_at` |
| `OrderItem` | 订单项 | `order` (FK), `recipe` (FK), `quantity`, `note` |

### 博客模型

| 模型 | 说明 | 关键字段 |
|------|------|----------|
| `Tag` | 标签 | `name`, `color` |
| `BlogPost` | 博客文章 | `title`, `slug`, `summary`, `content` (Markdown), `tags` (M2M), `is_published`, `is_featured`, `view_count` |

---

## 🔌 API 接口 (backend/api/urls.py)

### REST 端点

```
/api/recipes/          # RecipeViewSet - CRUD 菜谱
/api/ingredients/      # IngredientViewSet - CRUD 食材
/api/orders/           # OrderViewSet - CRUD 订单
/api/blog/posts/       # BlogPostViewSet - CRUD 博客
/api/blog/tags/        # TagViewSet - CRUD 标签
/api/chef/login/       # ChefAuthView - 厨师登录
/api/ai/chat/          # AiAgentView - AI 智能体（支持工具调用）
/api/ai/speciale/      # DeepSeekSpecialeView - DeepSeek V3.2 Speciale 思考模型
/api/ai/ocr/           # DeepSeekOCRView - 图片 OCR 识别（硅基流动 DeepSeek-OCR）
```

### 重要参数

- `?mode=chef` - 返回完整数据（含私密字段如 `chef_notes`、非公开菜谱）
- 不带 mode 参数 - 访客模式，只返回公开数据

### 博客特殊端点

- `GET /api/blog/posts/stats/` - 博客统计
- `GET /api/blog/posts/by-slug/{slug}/` - 通过 slug 获取文章

---

## 🛣️ 前端路由 (frontend/src/router/index.js)

### 公开路由（无需认证）

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | HomeView | 首页菜单 |
| `/my-orders` | MyOrdersView | 我的订单 |
| `/recipe/:id` | RecipeBookView | 菜谱详情（翻书阅读） |
| `/blog` | BlogListView | 博客列表 |
| `/blog/:slug` | BlogPostView | 博客文章详情 |
| `/ai-lab` | AiLabView | AI 实验室（DeepSeek V3.2 Speciale 思考模型） |
| `/chef/login` | ChefLoginView | 厨师登录 |

### 需认证路由 (`meta: { requiresAuth: true }`)

| 路径 | 组件 | 说明 |
|------|------|------|
| `/chef` | AdminLandingView | 厨师控制台首页 |
| `/chef/orders` | ChefDashboard | 订单管理 |
| `/chef/recipes` | RecipeManagerView | 菜谱管理 |
| `/chef/recipes/new` | RecipeEditorView | 新建菜谱 |
| `/chef/recipes/:id/edit` | RecipeEditorView | 编辑菜谱 |
| `/chef/inventory` | InventoryView | 库存管理 |
| `/chef/blog` | BlogManagerView | 博客管理 |
| `/chef/blog/new` | BlogEditorView | 新建博客 |
| `/chef/blog/:id/edit` | BlogEditorView | 编辑博客 |

---

## 🔐 认证机制

### 厨师登录 (简化版)

- **凭证来源**: `settings.py` 中的 `CHEF_USERNAME` 和 `CHEF_PASSWORD`（从环境变量读取）
- **默认凭证**: `chef` / `kitchen123`（仅开发环境）
- **Token**: SHA256 哈希生成的 32 字符 token
- **存储**: `localStorage` (`chef_token`, `chef_logged_in`)

### 前端认证状态 (frontend/src/store/auth.js)

```javascript
export const auth = reactive({
    isLoggedIn: localStorage.getItem('chef_logged_in') === 'true',
    token: localStorage.getItem('chef_token') || '',
    login(token) { ... },
    logout() { ... },
    checkAuth() { return this.isLoggedIn && this.token }
})
```

---

## 🛒 购物车状态 (frontend/src/store/cart.js)

```javascript
export const cart = reactive({
    items: [],                    // 购物车项 [{recipe, quantity, note}]
    customerName: '',             // 顾客名称（持久化到 localStorage）
    isOpen: false,                // 侧边栏开关
    myOrderIds: [],               // 已下订单 ID（持久化到 localStorage）
    
    addItem(recipe) { ... },
    removeItem(recipeId) { ... },
    updateNote(recipeId, note) { ... },
    async submitOrder() { ... }   // 提交订单到后端
})
```

---

## 🎨 关键 UI 组件

### MenuBook.vue - 翻书效果菜单
- 使用 `page-flip` 库实现
- 响应式适配：桌面端双页，移动端单页
- 触摸/滑动支持

### RecipeBookView.vue - 菜谱阅读器
- 全屏沉浸式体验
- 分页展示：封面 → 食材 → 步骤
- 滑动切换动画

### CartSidebar.vue - 购物车侧边栏
- 固定右侧滑出
- 实时编辑数量和备注

### AiChatWidget.vue - AI 智能点餐助手
- 悬浮气泡按钮（右下角）
- **工具调用**：支持 DeepSeek Function Calling
- 可执行操作：查看菜单、推荐菜品、添加购物车、下单
- 对话历史持久化到 localStorage
- 快捷操作按钮

### AiLabView.vue - AI 实验室（DeepSeek V3.2 Speciale）
- 独立全屏页面，浅色主题
- **思维链展示**：完整显示模型的推理过程
- 支持折叠/展开思维链
- 流式输出，实时显示思考过程和最终回答
- **图片 OCR**：支持上传/粘贴图片，自动识别数学题
- 统计信息：思考时长、字数等

---

## 🌐 API 配置

### 后端 CORS (backend/config/settings.py)
- 开发环境：`CORS_ALLOW_ALL_ORIGINS = True`
- 生产环境：通过 `CORS_ALLOWED_ORIGINS` 环境变量配置

### 前端 API 地址 (frontend/src/config/api.js)
```javascript
const API_BASE_URL = import.meta.env.PROD 
  ? ''                           // 生产环境：相对路径（Nginx 代理）
  : 'http://127.0.0.1:8000';    // 开发环境：本地后端
```

### Vite 开发代理 (frontend/vite.config.js)
```javascript
proxy: {
  '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
  '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true }
}
```

---

## 🚀 开发命令

### 后端
```bash
cd backend
source ../venv/bin/activate     # 激活虚拟环境
python manage.py runserver      # 启动开发服务器 (http://127.0.0.1:8000)
python manage.py migrate        # 数据库迁移
python manage.py seed_data      # 填充示例数据
```

### 前端
```bash
cd frontend
npm install                     # 安装依赖
npm run dev                     # 启动开发服务器 (http://localhost:5173)
npm run build                   # 构建生产版本 (输出到 dist/)
```

---

## 📝 关键设计决策

1. **厨师/访客模式区分**：通过 URL 参数 `?mode=chef` 控制数据可见性
2. **无传统用户系统**：厨师使用简单 token 认证，顾客无需注册
3. **订单追踪**：顾客订单 ID 存储在 localStorage，通过 `/my-orders` 查看
4. **博客 slug**：自动从标题生成，支持 Unicode
5. **图片上传**：Django media 文件夹，生产环境由 Nginx 静态服务

---

## ⚠️ 开发注意事项

1. **修改模型后**：需要 `makemigrations` 和 `migrate`
2. **添加新路由**：
   - 后端：在 `api/urls.py` 注册 ViewSet
   - 前端：在 `router/index.js` 添加路由，需认证的设置 `meta: { requiresAuth: true }`
3. **新增 API 字段**：同步更新 `serializers.py` 中的 `fields`
4. **样式修改**：使用 Tailwind 类名，遵循现有的 emerald/amber/stone 配色

---

## 📦 环境变量

### 后端 (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CHEF_USERNAME=chef
CHEF_PASSWORD=kitchen123
DB_ENGINE=django.db.backends.sqlite3
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_SPECIALE_BASE_URL=https://api.deepseek.com/v3.2_speciale_expires_on_20251215  # 可选，DeepSeek V3.2 Speciale 专用
SILICONFLOW_API_KEY=your-siliconflow-api-key  # 硅基流动 API（用于 DeepSeek-OCR 图片识别）
```

### 前端 (.env.production)
```env
VITE_API_URL=https://your_domain.com
```

