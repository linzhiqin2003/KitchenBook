---
name: ailab-interpretation
description: 同声传译与语音处理——语音转文字（ASR）、多语言翻译。当用户需要转录语音、翻译音频内容、处理录音文件时使用。
version: 1.0.0
metadata:
  hermes:
    tags: [asr, transcription, translation, speech, audio]
    category: productivity
    risk_level: low
    estimated_time: 30s
    requires_toolsets: [mcp]
---

# AI Lab 语音处理

使用 `ailab_transcribe` MCP 工具将语音转为文字。

## 功能

1. **语音转录** — 将音频/语音文件转换为文字
2. 支持多种语言：中文 (zh)、英文 (en)、日文 (ja)、韩文 (ko) 等

## 使用方式

### 语音转文字

```
mcp ailab ailab_transcribe audio_url="https://example.com/audio.webm" language="zh"
```

### 后续翻译

转录完成后，可使用 `ailab-chat` 技能进行翻译：

```
mcp ailab ailab_chat message="请将以下文字翻译成英文：{转录结果}"
```

## 支持的音频格式

- WebM（推荐）
- MP3
- WAV
- M4A
- OGG

## 注意事项

- 音频时长建议不超过 25MB
- 中文转录使用 `language="zh"`
- 转录质量受音频清晰度和背景噪音影响
- 如需实时同声传译，请使用现有的 Django WebSocket 服务（`/api/interpretation/`）
