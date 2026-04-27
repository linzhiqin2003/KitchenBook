---
name: ailab-chat
description: AI 智能对话——调用 DeepSeek V4 大模型进行问答、编程、写作、推理。支持 web_search 实时联网、thinking effort 控制、多模型切换。当用户需要 AI 对话、问问题、写代码、查资料、翻译、总结时使用。
version: 1.0.0
metadata:
  hermes:
    tags: [ai, chat, deepseek, coding, writing]
    category: productivity
    risk_level: low
    estimated_time: 30s
    requires_toolsets: [mcp]
    config:
      - key: ailab.default_model
        description: "默认模型"
        default: "deepseek-v4-flash"
        prompt: "选择默认 AI 模型"
      - key: ailab.default_thinking
        description: "默认思考强度"
        default: "low"
        prompt: "选择默认思考强度"
---

# AI Lab 智能对话

使用 `ailab_chat` MCP 工具与 DeepSeek 大模型对话。

## 模型选择

| 模型 | 适用场景 |
|------|---------|
| `deepseek-v4-flash` | 日常对话、快速问答、简单编程 |
| `deepseek-v4-pro` | 复杂推理、深度分析、长文本创作 |

## Thinking 控制

- `none` — 关闭思考（极速模式，适合简单任务）
- `low` — 轻度思考（默认，平衡速度与质量）
- `medium` — 中度思考
- `high` — 深度思考（复杂推理、数学题）
- `max` — 最大思考（科研级推理，耗时较长）

## 使用方式

直接调用 MCP 工具：

```
mcp ailab ailab_chat message="用户的问题" model="deepseek-v4-flash" thinking="low"
```

## 支持的场景

- 知识问答：历史、科学、文化、技术等
- 代码编写：Python、JavaScript、Go、Rust 等
- 文本创作：文章、邮件、文案、翻译
- 逻辑推理：数学题、编程题、分析问题
- 实时搜索：通过 web_search 获取最新信息
- 计算器：数学表达式计算

## 注意事项

- 工具会自动联网搜索（当需要实时信息时）
- 搜索结果会标注 [REF:n] 引用编号
- 复杂问题可调高 thinking 等级获得更好的推理质量
- API Key 由服务器统一管理，无需用户配置
