# QuestionGen 模块文档（KitchenBook）

## 1) 功能概览

QuestionGen 是项目中的“刷题/题目生成”子系统，包含：

- 多课程刷题（`course_id` 维度：如 `software-tools`、`c-programming`）
- 随机/按主题练习、难度筛选（`easy|medium|hard`）
- 服务端缓存题库（Django + DB），前端本地保存做题历史与已见题目集合（LocalStorage）
- AI 生成新题（DeepSeek `deepseek-chat`，要求返回 JSON）
- AI 答疑 / 审核（SSE 流式输出）；审核模式可建议删除题目，并通过 reasoner 二次确认后删除

---

## 2) 入口与路由

### 前端路由

- 页面入口：`/questiongen`
- 路由定义：`frontend/src/router/index.js`
- App 布局：`frontend/src/App.vue` 中对 `/questiongen` 使用“独立页面模式”（不渲染普通页头/导航）

### 后端路由

后端把 QuestionGen API 挂载到：

- `backend/config/urls.py`：`path("api/questiongen/", include("questions.urls"))`

因此 **最终 API 前缀**为：

- `/api/questiongen/`

> 注意：`backend/questions/views.py` 内 docstring 里写的是 `/api/questions/...`，但实际挂载在 `/api/questiongen/` 下；最终路径以 Django URLConf 为准。

---

## 3) 前端（Vue）模块说明

### API Client

- `frontend/src/api/questiongen.js`
  - `baseURL: '/api/questiongen'`
  - 提供 `questionApi.*` 方法（courses/topics/stats/smartNext/chat-stream/requestDelete 等）
- `frontend/src/api/index.js`
  - re-export `questionApi`

### 页面与组件

- `frontend/src/views/QuestionGenView.vue`
  - 负责课程选择、主题/随机练习模式、难度筛选、历史侧边栏、题目预取（prefetch）与会话去重逻辑
  - LocalStorage keys：
    - `questiongen_history`：答题历史（最近 100）
    - `questiongen_seen_ids`：已完成题目 id（最近 500）
    - `questiongen_selected_topic`：主题模式下当前主题
    - `questiongen_practice_mode`：`random|topic`
    - `questiongen_current_course`：当前课程 id

- `frontend/src/components/QuestionCard.vue`
  - 渲染题干/选项/解析（Markdown via `marked`）
  - 判定正确性（字符串包含/相等容错），提交后展示解析与反馈动画

- `frontend/src/components/QuestionSkeleton.vue`
  - 加载骨架屏

- `frontend/src/components/AIChatWindow.vue`
  - 仅在题目“已作答”后出现（浮动按钮 + 可调整大小窗口）
  - SSE 方式请求 `questionApi.getChatStreamConfig(...).url`（`/questions/chat-stream/`）
  - `mode=qa|review`：答疑/审核
  - 审核模式若检测到 `[RECOMMENDATION: DELETE]`，显示“确认删除”，调用 `questionApi.requestDelete`
  - 删除成功会向父组件 emit `question-deleted`，由 `QuestionGenView` 刷新题目与统计

### 样式

- `frontend/src/style.css`
  - `QuestionGen UI helpers`：`ios-card`、`option-btn`、`btn-primary` 等通用样式在刷题 UI 中使用

---

## 4) 后端（Django）模块说明

### Django App 挂载

- `backend/config/settings.py`
  - `INSTALLED_APPS` 包含 `"questions"`（QuestionGen 后端实现）

### URL 与 ViewSet

- `backend/questions/urls.py`
  - DRF `DefaultRouter()` 注册：`router.register(r'questions', QuestionViewSet)`
  - 因上层 prefix 为 `/api/questiongen/`，所以最终资源根为：`/api/questiongen/questions/`

- `backend/questions/views.py`
  - `QuestionViewSet`：提供 CRUD + 自定义 action

### 数据模型

- `backend/questions/models.py`
  - `Question`：`course_id/topic/difficulty/question_text/options/answer/explanation/seed_question/source_files/created_at`
  - 索引：`(course_id, topic)` 与 `(course_id, difficulty)`

- `backend/questions/serializers.py`
  - `QuestionSerializer`：对应前端展示字段

### 关键服务（questions/services）

#### 课程系统

- `backend/questions/services/courses.py`
  - 课程根目录：`{repo}/courses/`
  - 每门课结构：
    - `courses/{course-id}/courseware/`：课件 Markdown（可分子目录）
    - `courses/{course-id}/simulation/`：模拟题/种子题 Markdown
    - `courses/{course-id}/config.json`：课程元信息（可选 `topic_keywords`）

#### 课件/种子解析 & 主题推断

- `backend/questions/services/parser.py`
  - `parse_courseware(course_id)`：按主题聚合课件文本
  - `parse_simulation_questions(course_id)`：从 `simulation/*.md` 抽取“种子题”
  - `infer_topic(...)`：优先用 DeepSeek 进行 topic 分类；失败则基于关键词匹配

#### AI 生成题目

- `backend/questions/services/generator.py`
  - DeepSeek OpenAI 兼容客户端：
    - `BASE_URL = "https://api.deepseek.com/v1"`
    - 读取 `DEEPSEEK_API_KEY`（`backend/.env`）
  - `generate_question(seed_question, course_id, target_difficulty)`：
    - 基于 `seed_question` 风格，但强制围绕 `courseware` 内容生成新题
    - 要求输出 JSON（topic/difficulty/question/options/answer/explanation）
  - `generate_question_for_topic(topic, ...)`：主题模式直接生成指定 topic 的题

#### AI Chat（SSE）

- `backend/questions/services/chat.py`
  - `chat_stream(mode, messages, current_question, course_id)`：对 deepseek-chat 进行 `stream=True` 流式输出
  - `chat_review_mode(...)`：审核模式会在文本中夹带 `[RECOMMENDATION: DELETE]` 作为“建议删除”信号
  - `confirm_deletion_with_reasoner(...)`：二次确认用 `deepseek-reasoner`，默认失败时保守不删

### 主要 API（最终路径）

以下均在 `/api/questiongen/` 前缀下：

- `GET  /questions/courses/`：课程列表 + 默认课程
- `GET  /questions/`：题库列表（可选 `?course_id=`）
- `GET  /questions/{id}/`：单题
- `POST /questions/generate/`：基于 seed（可空）生成新题并入库
- `POST /questions/smart-next/`：智能下一题（优先返回缓存，空则生成）
- `POST /questions/batch-generate/`：批量生成并入库
- `GET  /questions/topics/`：topics（db topics + courseware topics）
- `GET  /questions/stats/`：缓存题数量统计（按 topic/course）
- `POST /questions/chat/`：非流式 AI Chat
- `POST /questions/chat-stream/`：SSE 流式 AI Chat（前端使用）
- `POST /questions/{id}/request-delete/`：请求删除（reasoner 二次确认后可能删除）

---

## 5) 课程数据（courses/）说明

当前仓库已存在课程示例（目录：`courses/`）：

- `software-tools`：课件在 `courseware/` 的多个主题子目录，模拟题在 `simulation/`
- `c-programming`：课件为扁平 markdown 文件，模拟题在 `simulation/`

`parser.parse_courseware()` 会根据是否存在子目录来决定“按目录聚合”或“按文件聚合”。

---

## 6) QuestionGen 相关代码文件清单（完整）

> 说明：此清单按“前端/后端/脚本”归类；其中后端核心实现为 Django app `backend/questions/`，通过 `/api/questiongen/` 对外提供服务。

### 前端

- `frontend/src/router/index.js`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `frontend/src/api/index.js`
- `frontend/src/api/questiongen.js`
- `frontend/src/views/QuestionGenView.vue`
- `frontend/src/components/QuestionCard.vue`
- `frontend/src/components/QuestionSkeleton.vue`
- `frontend/src/components/AIChatWindow.vue`

### 后端（Django）

- `backend/config/settings.py`
- `backend/config/urls.py`
- `backend/questions/__init__.py`
- `backend/questions/admin.py`
- `backend/questions/apps.py`
- `backend/questions/models.py`
- `backend/questions/serializers.py`
- `backend/questions/tests.py`
- `backend/questions/urls.py`
- `backend/questions/views.py`
- `backend/questions/migrations/__init__.py`
- `backend/questions/migrations/0001_initial.py`
- `backend/questions/migrations/0002_add_source_files.py`
- `backend/questions/migrations/0003_add_course_id.py`
- `backend/questions/migrations/0004_add_difficulty.py`
- `backend/questions/services/__init__.py`
- `backend/questions/services/courses.py`
- `backend/questions/services/parser.py`
- `backend/questions/services/generator.py`
- `backend/questions/services/chat.py`

### 辅助脚本（与 DeepSeek/流式相关，可能用于调试）

- `test_deepseek.py`

---

## 7) 快速搜索命令（复现“完整清点”）

在仓库根目录执行：

```bash
# 1) 直接包含 questiongen 关键字的文件
rg -n -i "questiongen" . --hidden --glob '!.git/**' --glob '!node_modules/**'

# 2) 前端调用点（API wrapper / SSE / 删除）
rg -n "questionApi|getChatStreamConfig|requestDelete|smartNext" frontend/src -S

# 3) 后端挂载点（/api/questiongen -> questions.urls）
rg -n "api/questiongen|include\\(\"questions\\.urls\"\\)|INSTALLED_APPS" backend -S
```

---

## 8) 备注：`backend/questiongen-data/`

仓库里还有 `backend/questiongen-data/` 目录，内容看起来是课件/实验/模拟题数据的历史版本（例如 `01-sysadmin/`、`03-regex/`、`08-sql/` 等）。

当前后端代码的课程系统 **读取的是仓库根目录的 `courses/`**（见 `backend/questions/services/courses.py`），并未直接引用 `backend/questiongen-data/`；如需清理/迁移，请先全仓搜索确认是否有外部脚本依赖该目录。

