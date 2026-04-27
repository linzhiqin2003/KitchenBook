---
name: ailab-emoji
description: 表情包视频生成——上传人像图片，套用动态表情模板生成 GIF/视频表情。当用户想要制作表情包、生成动态表情、做人脸动画时使用。
version: 1.0.0
metadata:
  hermes:
    tags: [emoji, video, face, gif, meme, generation]
    category: entertainment
    risk_level: low
    estimated_time: 60s
    requires_toolsets: [mcp]
---

# AI Lab 表情包生成

使用 `ailab_emoji_generate` MCP 工具生成动态表情包。

## 功能

上传一张人像照片，选择表情模板，AI 会生成对应的动态表情包视频。

## 可用模板

| 模板 ID | 说明 |
|---------|------|
| `mua` | 飞吻 |
| `whistle` | 吹口哨 |
| `wink` | 眨眼 |
| `cute` | 可爱 |
| `kiss` | 亲吻 |
| `angry` | 生气 |

> 完整模板列表可通过 ailab MCP 服务查询。

## 使用方式

```
mcp ailab ailab_emoji_generate template_id="wink" image_url="https://example.com/face.jpg"
```

## 注意事项

- 图片需包含清晰的正脸
- 生成时间约 10-30 秒
- 需要 DashScope API Key（服务器已配置）
- 图片 URL 需可公开访问
