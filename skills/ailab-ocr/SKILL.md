---
name: ailab-ocr
description: 图片文字识别——将图片中的文字、公式、表格识别为 Markdown 格式。当用户需要提取图片中的文字、识别截图、转换扫描件、OCR 时使用。
version: 1.0.0
metadata:
  hermes:
    tags: [ocr, image, text-extraction, markdown, document]
    category: productivity
    risk_level: low
    estimated_time: 15s
    requires_toolsets: [mcp]
---

# AI Lab 图片识别

使用 `ailab_ocr` MCP 工具将图片中的文字转换为 Markdown。

## 功能

1. **文字提取** — 从图片中提取所有文字内容
2. **公式保留** — 数学公式转换为 LaTeX 格式
3. **表格识别** — 表格转换为 Markdown 表格
4. **结构保留** — 尽量保留原文的排版结构

## 使用方式

```
mcp ailab ailab_ocr image_url="https://example.com/document.png"
```

## 支持的图片格式

- PNG（推荐）
- JPEG / JPG
- WebP
- BMP

## 典型场景

- 截图中的代码/错误信息提取
- 纸质文档扫描件数字化
- 试卷/题目图片转文字
- PPT/白板照片内容提取
- 手写笔记识别

## 注意事项

- 图片大小建议不超过 10MB
- 图片 URL 需可公开访问
- 使用 DeepSeek-OCR 模型（通过 SiliconFlow）
- 识别结果保留原始 Markdown 格式（公式、表格等）
