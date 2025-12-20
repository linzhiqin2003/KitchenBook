# 📖 LZQ 个人网站 - lzqqq.org

一个集博客、AI 工具、学习笔记、私人厨房于一体的多功能个人平台。

> 🌐 **在线访问**: 
> - 主站: [www.lzqqq.org](https://www.lzqqq.org)
> - 厨房: [www.lzqqq.org/kitchen](https://www.lzqqq.org/kitchen)
> - 博客: [www.lzqqq.org/blog](https://www.lzqqq.org/blog)
> - 刷题: [www.lzqqq.org/questiongen](https://www.lzqqq.org/questiongen)

## ✨ 核心模块

### 🍳 私人厨房 (`/kitchen`)
私人菜谱收藏，具有拟物化的翻书效果，记录喜欢的美食制作方法。
- 菜谱展示与管理
- 翻书阅读效果
- 订单管理系统
- AI 实验室 (`/kitchen/ai-lab`)

### 📝 技术博客 (`/blog`)
分享技术探索与学习心得：
- Markdown 写作支持
- 标签分类系统
- 暗色/亮色主题切换
- 精选文章展示

### 🤖 AI 实验室 (`/kitchen/ai-lab`)
基于 DeepSeek API 构建的 AI 对话工具：
- **思维链推理**: 展示 AI 的推理过程，支持折叠/展开
- **多模态输入**: 支持图片上传与 OCR 识别
- **语音交互**: 语音录制转文字
- **数学公式渲染**: 使用 MathJax 支持 LaTeX 公式
- **Markdown 渲染**: 完整的 Markdown 语法支持

### 📚 智能刷题 (`/questiongen`)
AI 驱动的智能学习工具，帮助巩固课程知识：
- **智能出题**: 基于课程材料自动生成练习题
- **多课程支持**: 灵活切换不同学习课程
- **主题筛选**: 按知识点专项练习
- **难度分级**: 支持简单/中等/困难三级难度
- **答案解析**: 详细的答案解释与来源引用

## 🛠️ 技术栈

**前端:**
- Vue 3 + Vite
- Tailwind CSS
- Vue Router + Pinia
- page-flip (翻书效果)
- MathJax (数学公式)

**后端:**
- Django 5.2 + Django REST Framework
- DeepSeek API (AI 能力)
- PostgreSQL / SQLite
- Pillow (图片处理)

**部署:**
- Nginx + Gunicorn
- Cloudflare (DNS + SSL)

## 🚀 本地开发

### 1. 克隆项目

```bash
git clone https://github.com/linzhiqin2003/KitchenBook.git
cd KitchenBook
```

### 2. 启动后端

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 SECRET_KEY 和 DEEPSEEK_API_KEY

# 数据库迁移
python manage.py migrate

# 启动开发服务器
python manage.py runserver
```

### 3. 启动前端

```bash
# 新开一个终端
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173` 即可预览。

## 📂 URL 结构

```
www.lzqqq.org/
├── /kitchen                 # 私人厨房首页
│   ├── /my-orders          # 我的订单
│   ├── /recipe/:id         # 菜谱详情
│   ├── /ai-lab             # AI 实验室
│   └── /chef               # 管理后台
│       ├── /orders         # 订单管理
│       ├── /inventory      # 库存管理
│       ├── /recipes        # 食谱管理
│       └── /blog           # 博客管理
├── /blog                    # 博客列表
│   └── /:slug              # 博客文章
└── /questiongen            # 智能刷题
```

## 📖 更多文档

- [完整部署教程](DEPLOYMENT.md) - 服务器部署指南
- [更新指南](UPDATE_GUIDE.md) - 网站更新流程

## 📜 许可

MIT License

---

*持续学习，不断进步。* 🚀
