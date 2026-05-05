# ailab MCP Server

将 MyWeb ailab 的 AI 能力暴露为 MCP 工具，供 Hermes Agent 或其他 MCP 客户端调用。

## 安装

```bash
cd backend
pip install -r mcp_server/requirements.txt
```

## 启动

### stdio 模式（默认，供 Claude Code / Hermes Agent 调用）

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings python -m mcp_server.server
```

### HTTP 模式（供远程客户端调用）

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings python -m mcp_server.server --transport http --port 8100
```

### 使用 fastmcp CLI

```bash
cd backend
fastmcp run mcp_server/server.py:mcp --transport http --port 8100
```

## 可用工具

| 工具 | 说明 |
|------|------|
| `ailab_search_recipes` | 搜索菜谱 |
| `ailab_get_blog_posts` | 获取博客文章 |

## 测试

```bash
# 列出所有工具
fastmcp inspect mcp_server/server.py:mcp

# 测试单个工具
fastmcp call mcp_server/server.py ailab_search_recipes query="番茄炒蛋"
```

## 注册到 Hermes Agent

在 `~/.hermes/config.yaml` 中添加：

```yaml
mcp_servers:
  ailab:
    command: python
    args:
      - -m
      - mcp_server.server
    cwd: /path/to/MyWeb/backend
    env:
      DJANGO_SETTINGS_MODULE: config.settings
```
