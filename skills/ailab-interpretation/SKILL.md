---
name: ailab-interpretation
description: 同声传译——实时音频流式转译。支持双 ASR 引擎（VAD 逐句 + Tingwu 实时），WebSocket 流式推送，边听边译边显。当用户需要同声传译、实时翻译会议、听译音频时使用。
version: 1.0.0
metadata:
  hermes:
    tags: [interpretation, real-time, asr, translation, speech, websocket]
    category: productivity
    risk_level: low
    estimated_time: N/A
    requires_toolsets: [web]
---

# AI Lab 同声传译

这是一套完整的**实时音频流式转译系统**，不是简单的音频文件转文字。

## 架构

```
浏览器麦克风 ──WebSocket──→ Daphne (ASGI) ──→ VAD 逐句切分
                                              ├── Qwen ASR 实时识别
                                              ├── Qwen MT 翻译
                                              └── WebSocket 推送结果
```

## 两种工作模式

### 1. 实时同声传译（WebSocket — 主力模式）

部署在 `wss://www.lzqqq.org/ws/interpretation/`（Daphne 服务）。

- **双引擎 ASR**：
  - Standard (VAD) — 逐句切分，识别后翻译，适合会议场景
  - Tingwu — 通义听悟实时流式，延迟更低
- **双管道并行**：快速管道逐句出结果，慢速管道积累上下文后给出更准确版本
- **多语言支持**：中/英/日/韩/德/法/西/俄/葡/阿拉伯/意大利/印地/印尼/泰/土/乌克兰/越
- **Django WebSocket Consumer**（`apps/interpretation/consumers.py`）处理全双工通信

访问方式：打开 `https://www.lzqqq.org/ai-lab/studio` 使用浏览器端。

### 2. 文件音频转文字（REST API）

使用 `ailab_transcribe` MCP 工具处理已录制的音频文件：

```
mcp ailab ailab_transcribe audio_url="https://example.com/audio.webm" language="zh"
```

这是降级模式，适合处理录音文件、语音笔记等非实时场景。

## 翻译 & 润色（REST API）

后端 `/api/interpretation/` 还提供：
- `POST /refine/` — 文本润色
- `POST /translate/` — 文本翻译
- `POST /transcribe-translate/` — 文件上传 → 转写 → 翻译 一条龙

## 服务运行状态

- Daphne WebSocket 服务由 systemd 管理：`sudo systemctl status daphne`
- Django 路由：`/ws/interpretation/` → `InterpretationConsumer`
- 前端入口：`AiLabStudioView.vue`（Vue 3 + Tailwind）

## 注意事项

- 实时传译需要浏览器麦克风权限（HTTPS）
- Tingwu 模式依赖阿里云 AccessKey
- 翻译依赖 DashScope API（DASHSCOPE_API_KEY）
- 这不是一个可被 Agent "调用"的工具——它是持续运行的 WebSocket 服务
