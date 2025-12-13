# 📖 KitchenBook - 个人网站

我的个人网站项目，一个集博客、AI 工具、学习笔记于一体的多功能平台。

> 🌐 **在线访问**: [your-domain.com](https://your-domain.com)

## ✨ 核心功能

### 📝 技术博客
分享我的技术探索与学习心得，支持 Markdown 写作、标签分类、暗色主题切换，以及精选文章展示。

### 🤖 AI 实验室
基于 DeepSeek API 构建的 AI 对话工具，集成了以下能力：
- **思维链推理**: 展示 AI 的推理过程，支持折叠/展开
- **多模态输入**: 支持图片上传与 OCR 识别
- **语音交互**: 语音录制转文字
- **数学公式渲染**: 使用 MathJax 支持 LaTeX 公式
- **Markdown 渲染**: 完整的 Markdown 语法支持

### 📚 智能刷题 (QuestionGen)
AI 驱动的智能学习工具，帮助我巩固课程知识：
- **智能出题**: 基于课程材料自动生成练习题
- **多课程支持**: 灵活切换不同学习课程
- **主题筛选**: 按知识点专项练习
- **难度分级**: 支持简单/中等/困难三级难度
- **答案解析**: 详细的答案解释与来源引用

### 🍳 菜谱书
私人菜谱收藏，具有拟物化的翻书效果，记录我喜欢的美食制作方法。

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
- Let's Encrypt (SSL)

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

## 📂 项目结构

```
KitchenBook/
├── backend/                 # Django 后端
│   ├── api/                # 核心 API (菜谱、博客等)
│   ├── questions/          # 智能刷题模块
│   ├── questiongen-data/   # 课程材料数据
│   └── config/             # Django 配置
├── frontend/               # Vue 前端
│   ├── src/views/          # 页面组件
│   │   ├── AiLabView.vue        # AI 实验室
│   │   ├── QuestionGenView.vue  # 智能刷题
│   │   ├── BlogListView.vue     # 博客列表
│   │   └── ...
│   ├── src/components/     # 可复用组件
│   └── src/router/         # 路由配置
├── deploy/                 # 部署配置
├── DEPLOYMENT.md           # 部署文档
└── README.md
```

## 📖 更多文档

- [完整部署教程](DEPLOYMENT.md) - 服务器部署指南
- [更新指南](UPDATE_GUIDE.md) - 网站更新流程

## 📜 许可

MIT License

---

*持续学习，不断进步。* 🚀
