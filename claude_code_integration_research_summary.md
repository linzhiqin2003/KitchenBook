# Claude Code 额度共享与集成方式调研总结

## 1. 开源项目利用 Claude 套餐额度的方式对比

| 项目 | 直接 API Key | CLI 凭证复用 | 订阅绑定 |
|------|-------------|-------------|---------|
| **OpenClaw** | `anthropic/*` 模型 + API Key | Claude CLI Backend（复用本机已登录会话） | 无 |
| **Hermes** | Anthropic Provider + API Key | Claude Code Skill（委托给 `claude` 子进程） | Claude Max OAuth |
| **OpenCode** | `ANTHROPIC_API_KEY` | `claude-cli` / `claude-api` 提供者 | `@life-ai-tools/opencode-claude` 插件 |
| **KiloCode** | Anthropic Provider + API Key | 曾支持，2026/01 后 Anthropic 限制 CLI 仅供官方客户端 | 无 |

**核心模式**：
- **API Key 直连**：最稳定、官方支持，按 token 计费。
- **CLI 凭证复用**：省 Key，但 Anthropic 已收紧政策，且额外用量仍扣费。
- **Wrapper/Bridge**：将 Claude CLI 包装为 OpenAI 兼容 HTTP 服务（如 `hermes-shim-http`）。

---

## 2. Claude Code CLI 底层通信机制

基于社区逆向工程（`ghboke/claude-code-reverse` 对 v2.1.88 的 source map 还原）：

### 2.1 基本通信
- **协议**：标准 HTTPS + SSE（Server-Sent Events）流式响应
- **SDK**：底层使用 `@anthropic-ai/sdk`
- **请求头**：
  ```
  x-app: 'cli'
  User-Agent: claude-code/{version}
  X-Claude-Code-Session-Id: {sessionId}
  x-client-request-id: {uuid}
  Authorization: Bearer {token}
  ```

### 2.2 认证机制
| 方式 | 存储位置 | Token 格式 |
|------|---------|-----------|
| OAuth（Pro/Max 订阅） | macOS Keychain / `~/.claude/.credentials.json` | `sk-ant-oat01-...` |
| API Key | 同上 | `sk-ant-api03-...` |

### 2.3 请求体特点
- **Prompt Caching**：系统提示词拆分为"静态部分"（全局缓存，1h TTL）和"动态部分"（会话特定）
- **Metadata**：每个请求携带 `device_id`、`account_uuid`、`session_id`，Anthropic 后端据此统计用量
- **Beta 特性**：`prompt-caching`、`interleaved-thinking`、`fast-mode`、`tool-search` 等

### 2.4 拦截手段
- 设置 `ANTHROPIC_BASE_URL` 指向本地代理（mitmproxy）
- 系统级抓包（Charles、Wireshark + 本地根证书）

---

## 3. OAuth Token 能否直接发 API 请求

**结论：不能直接发，Anthropic 已在服务端封堵。**

- 官方 Messages API **不识别** `sk-ant-oat01-...` OAuth Token，返回 401。
- 社区曾发现用 `Authorization: Bearer sk-ant-oat01-...` + CLI header 有时可绕过，但 Anthropic 现已返回：
  ```
  400: This credential is only authorized for use with Claude Code
  ```
- Anthropic 后端同时校验**凭证类型**和**请求上下文**（session、device、行为指纹），不是只匹配 header。

**替代思路**：不直接发 HTTP，而是**驱动 Claude Code 二进制本身**（`claude mcp serve` 或 `claude -p`），让官方 CLI 作为实际请求方。

---

## 4. 多人共享一个 Claude Code 账号

### 4.1 技术可行性
- **可以启动**：Claude Code 不限制设备数，订阅绑定账号。
- **速率限制是账号级共享池**：多人同时用 = N 倍速消耗额度，一人用完全员限流。
- **OAuth Refresh Token 竞态条件**：`refresh token` 为一次性，多设备并发时频繁触发重新登录（Anthropic issue #24317）。

### 4.2 政策风险
- Anthropic ToS 明确**个人订阅不允许多人共享**。
- 多 IP、多设备指纹同时登录会触发风控，可能导致账号锁定。

---

## 5. 服务器中转方案

### 5.1 方案对比

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **SSH + 各跑 claude** | 用户 SSH 上服务器各自运行 | 简单 | 额度竞争、隐私混乱、OAuth 冲突 |
| **`claude mcp serve`** | 官方 MCP 服务器模式 | 标准协议 | 会话隔离需自建、仍是共享额度 |
| **HTTP Wrapper around `claude -p`** | 收到请求后 spawn 子进程 | 完全可控、可排队 | 冷启动慢、上下文不连续 |
| **OpenClaw CLI Backend** | OpenClaw 调用服务器上的 `claude` 二进制 | 现成方案 | 配置复杂 |
| **`claude remote-control`** | 官方远程会话 | 单人跨设备 | **不设计为多人共享** |

### 5.2 推荐架构（如确需中转）

```
用户请求 → Nginx/Caddy（鉴权）→ HTTP Wrapper（队列 + 会话管理）
                                        ↓
                              Claude Code（已登录）
                                        ↓
                                   Anthropic API
```

### 5.3 关键建议
1. **服务器上直接用 `claude login` 或 `claude setup-token`**，避免多设备 OAuth refresh 竞态。
2. **请求队列化**：Claude Code 并发支持差，wrapper 层做串行化或限流。
3. **监控额度**：共享账号消耗速度 = 人数倍速，接近上限时告警。
4. **更务实的替代**：团队长期用建议走 **API Key + IDE 插件（OpenClaw/Cline/Continue）**，用量可见可控，无 CLI 并发限制。

---

## 参考资源

- `ghboke/claude-code-reverse` — Claude Code v2.1.88 逆向工程报告
- `openclaw/openclaw` issue #559 — OAuth tokens blocked for external API use
- `anthropics/claude-code` issue #24317 — OAuth refresh token race condition
- Claude Code Docs — Remote Control、Headless Mode、MCP
