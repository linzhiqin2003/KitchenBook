## 后端接口文档

### 接口列表

1. /api/interpretation/health/	应用后端健康检查

​	测试用例：`curl -s https://www.lzqqq.org/api/interpretation/health/ | jq `

```json
return {
  "status": "ok",
  "api_key_configured": true
}
```

2. /api/interpretation/tts-voices/	tts-voices接口提供的声音列表	

​	测试示例：`curl -s https://www.lzqqq.org/api/interpretation/tts-voices/ | jq`

```json
return {"voices": [
    {
      "id": "Cherry",
      "gender": "female",
      "style": "warm",
      "description": "芊悦 - 阳光积极、亲切自然的女声",
      "emoji": "🌸"
    },...}
```

2. 