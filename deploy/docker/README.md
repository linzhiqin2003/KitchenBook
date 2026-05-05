# ailab Hermes Agent — 容器化部署

把原本以 systemd user unit 直跑的 Hermes Agent 包进 docker，达到：

- **沙盒隔离**：Hermes 在容器内任意工具调用、写文件、跑 shell 都不影响 host
- **资源上限**：内存 / CPU / PID 数硬限，agent 失控不会拖死服务器
- **可重建**：上游版本 + 17 个 patch 全部固化进镜像，可重复部署
- **MCP server 解耦**：MCP server 留在 host 上跑（直连 SQLite，无需进容器）

## 拓扑

```
公网
  └→ nginx (host)
       └→ /hermes/   → 127.0.0.1:8642 ───┐
       └→ /api/      → 127.0.0.1:8004   │
                                         │
host                                     │
  ├─ systemd: gunicorn          :8004   │
  ├─ systemd: ailab-mcp         :8100   │  (HTTP MCP transport)
  ├─ systemd: hermes-docker             │
  │   └─ docker compose up              │
  │       └─ container ailab-hermes ←───┘
  │           └→ host.docker.internal:8004  (Django callback)
  │           └→ host.docker.internal:8100  (MCP)
  └─ /home/admin/.hermes/  ← bind mount → /opt/data
```

## 文件清单

```
deploy/docker/
├── Dockerfile.ailab              # 三阶段：clone 上游 → patch → runtime
├── docker-compose.yml            # bridge 网络 + 资源上限 + 安全收紧
├── apply-patches-container.sh    # build 时 sed 改路径再 apply 17 个 patch
├── .env.example                  # HERMES_UID/GID、HERMES_INTERNAL_TOKEN 等
├── .dockerignore                 # 减小 build context
└── README.md                     # 本文件

deploy/systemd/
├── ailab-mcp.service             # MCP server (HTTP transport)
└── hermes-docker.service         # 替代旧 user unit hermes-gateway.service
```

---

## 一、首次部署（服务器 / Linux）

服务器目标：`ssh myserver` (Alibaba Cloud Linux 3, 3.5GB RAM)

### 1. 服务器装 docker（一次性）

```bash
ssh myserver
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo \
    https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker admin
# 重登录使 docker 组生效
exit
ssh myserver
docker --version && docker compose version  # 验证
```

### 2. 装 MCP server 缺失依赖（host 侧）

```bash
ssh myserver
cd /home/admin/KitchenBook
source venv/bin/activate
pip install -r backend/mcp_server/requirements.txt   # fastmcp 等
deactivate
```

### 3. 部署 systemd unit

```bash
ssh myserver
cd /home/admin/KitchenBook
git pull   # 拉本次 PR

sudo cp deploy/systemd/ailab-mcp.service /etc/systemd/system/
sudo cp deploy/systemd/hermes-docker.service /etc/systemd/system/
sudo systemctl daemon-reload

# 准备 .env —— HERMES_INTERNAL_TOKEN 沿用旧 user unit 里的值
HERMES_TOKEN=$(grep HERMES_INTERNAL_TOKEN ~/.config/systemd/user/hermes-gateway.service \
               | sed 's/.*=//;s/"//g')
cd /home/admin/KitchenBook/deploy/docker
cp .env.example .env
sed -i "s|^HERMES_INTERNAL_TOKEN=.*|HERMES_INTERNAL_TOKEN=${HERMES_TOKEN}|" .env

# 关停旧 hermes-gateway（user unit），8642 端口让出来
systemctl --user stop hermes-gateway.service
systemctl --user disable hermes-gateway.service
```

### 4. 修改 hermes config —— 把 MCP transport 改为 HTTP

```bash
# 备份
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%s)

# 编辑 mcp_servers.ailab 段，参考 skills/hermes-config.yaml 模板
$EDITOR ~/.hermes/config.yaml
```

把这段：
```yaml
mcp_servers:
  ailab:
    command: /home/admin/KitchenBook/venv/bin/python
    args: [-m, mcp_server.server]
    cwd: /home/admin/KitchenBook/backend
    env: {DJANGO_SETTINGS_MODULE: config.settings, PYTHONPATH: /home/admin/KitchenBook/backend}
```

改成：
```yaml
mcp_servers:
  ailab:
    transport: streamable-http
    url: http://host.docker.internal:8100/mcp
    timeout: 60
```

并确认 `skill_paths` 包含 `/opt/ailab-skills`（容器内路径）。

### 5. Snapshot host 上 hermes 源码 + 构建镜像 + 启动

> 为什么不在容器里 git clone + apply patches：上游 hermes 持续演化，
> 部分 patch anchor 在新 commit 里被收编/重构。host 上的 apply.sh 是
> idempotent，已经把状态固化在文件里。镜像直接 snapshot host 当前能跑
> 的源码，跟生产状态完全一致，最稳。

```bash
# 5.1 Snapshot host 源码到 build context（排除 venv/node_modules/.git/*.bak）
bash /home/admin/KitchenBook/deploy/docker/prepare-source.sh
# 输出类似：done — 2841 files, 45M

# 5.2 Build (服务器内存 3.5GB+2GB swap 够；预计 10–15 分钟)
cd /home/admin/KitchenBook/deploy/docker
sudo docker compose build 2>&1 | tee /tmp/hermes-build.log

# 5.3 启动新 services
sudo systemctl enable --now ailab-mcp.service
sudo systemctl enable --now hermes-docker.service

# 验证
systemctl status ailab-mcp.service hermes-docker.service
docker ps | grep ailab-hermes
docker logs --tail=50 ailab-hermes
curl -fsS http://127.0.0.1:8100/mcp/ -X POST -H 'content-type: application/json' \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq .
curl -fsS http://127.0.0.1:8642/api/tools \
    -H "Authorization: Bearer ailab-hermes-2026" | jq '. | length'
```

### 6. 端到端验证（前端 AI Lab）

打开 https://www.lzqqq.org/ai-lab/，发一条测试消息。检查：
- 消息能正常返回（chat completions 流）
- Hermes 能调到 ailab MCP 工具（如让它 `搜索菜谱 番茄炒蛋`）
- `docker logs ailab-hermes` 没报错
- `journalctl -u ailab-mcp.service -f` 看到 MCP 请求

---

## 二、Mac 开发环境

```bash
cd /Users/linzhiqin/Codespace/MyProject/MyWeb/deploy/docker
cp .env.example .env

# 编辑 .env：
#   HERMES_HOST_DATA=/Users/linzhiqin/.ailab-hermes
#   HERMES_UID=$(id -u)         # 通常 501
#   HERMES_GID=$(id -g)         # 通常 20
#   HERMES_INTERNAL_TOKEN=<随便生成一个，前后端一致即可>

mkdir -p /Users/linzhiqin/.ailab-hermes
docker compose build
docker compose up -d
docker compose logs -f hermes
```

Mac 上 Django 用 `python manage.py runserver 0.0.0.0:8000`，
前端 `frontend/src/config/api.js` HERMES_API_URL 走 `http://127.0.0.1:8642`。

> ⚠️ Mac 上 MCP server 不通过 systemd 跑，开发时手动起一个：
> ```bash
> cd backend && DJANGO_SETTINGS_MODULE=config.settings \
>     ../venv/bin/python -m mcp_server.server --transport http --host 0.0.0.0 --port 8100
> ```
> 注意 host 必须是 `0.0.0.0` 才能让容器访问到。

---

## 三、日常运维

### 升级 Hermes 上游版本

```bash
# 1. host 上正常升级（git pull + apply.sh），确保 host 模式能跑
cd ~/.hermes/hermes-agent && git pull
cd /home/admin/KitchenBook && bash deploy/hermes-patches/apply.sh
systemctl --user restart hermes-gateway   # 验证 host 模式 OK

# 2. snapshot 新源码进 build context
bash deploy/docker/prepare-source.sh

# 3. 重 build + 重启容器
cd deploy/docker
sudo docker compose build
sudo systemctl restart hermes-docker.service
```

如果 patch 在 host 上已经 fail（anchor not found），先修
`deploy/hermes-patches/<n>_*.py` 让 host 模式能跑，再 snapshot。

### 查日志

```bash
docker logs --tail=200 -f ailab-hermes              # Hermes
journalctl -u ailab-mcp.service -f                  # MCP
journalctl -u hermes-docker.service                 # 容器 lifecycle
```

### 进容器排错

```bash
docker exec -it ailab-hermes bash
# 容器里能 cat /opt/data/config.yaml、看 sessions、跑 hermes cli 等
```

### 重启

```bash
sudo systemctl restart hermes-docker.service        # 重建容器
docker compose -f deploy/docker/docker-compose.yml restart hermes  # 仅重启进程
```

---

## 四、回滚到旧 systemd user unit

容器跑挂了想立刻回原方案，**3 步、零数据丢失**（`~/.hermes/` 是 bind mount 不动）：

```bash
# 1. 停容器
sudo systemctl stop hermes-docker.service
sudo systemctl disable hermes-docker.service

# 2. 把 ~/.hermes/config.yaml 的 mcp_servers.ailab 改回 stdio 形式
$EDITOR ~/.hermes/config.yaml
# (从 ~/.hermes/config.yaml.bak.* 还原即可)

# 3. 起回旧 user unit
systemctl --user enable --now hermes-gateway.service
systemctl --user status hermes-gateway.service

# 同时停掉新增的 ailab-mcp（旧方案是 stdio，不需要它）
sudo systemctl stop ailab-mcp.service
sudo systemctl disable ailab-mcp.service
```

---

## 五、安全边界总结

| 维度 | 配置 | 内部 / 外部影响 |
|---|---|---|
| 文件系统 | bind mount `~/.hermes:/opt/data` + `skills:ro` | 容器内可读写 `/opt/data` 和 `/tmp`；**写不到** host 上的 `~/KitchenBook`、`/etc`、其他用户家目录 |
| 网络 | 自定义 bridge + 端口仅 loopback publish | 容器能出网调 LLM API；公网通过 nginx 反代访问，不能直连 |
| 用户 | UID 1000（重映射到 admin），非 root | 工具能跑，但容器内不是 root |
| 权限 | `no-new-privileges:true`，无 docker.sock 挂载 | **不能** 提权，**不能** 起兄弟容器逃逸 |
| 资源 | 1.5GB RAM / 2 CPU / 2048 PID | agent 失控也不会拖死服务器 |
| 日志 | json-file 10MB×3 滚动 | 不会把磁盘写爆 |

> ⚠️ 上游 Hermes 镜像默认带 `docker-cli` 二进制（用于 `terminal.backend=docker`）。
> 我们的 Dockerfile **去掉了 docker-cli**，并且不挂 `/var/run/docker.sock`，
> 即便恶意工具调用也无法操作 host 上的 docker。`terminal.backend` 已设为 `local`，
> Hermes 工具只在容器内 fork 进程。

---

## 六、已知坑

1. **首次启动慢**：上游 entrypoint 会从 `cli-config.yaml.example` cp 模板，并跑 `tools/skills_sync.py`。如果 `~/.hermes/config.yaml` 已存在则跳过 —— 服务器现有数据不受影响。
2. **MCP HTTP transport 字段名**：fastmcp 用 `streamable-http`。如果 Hermes 某版本不识别，看 `docker logs ailab-hermes` 报的错，可能要试 `transport: http`。
3. **patch 路径硬编码**：未来在 `deploy/hermes-patches/` 加新 patch 时，仍然按 host 路径写（`/home/admin/.hermes/hermes-agent/...`），构建时 `apply-patches-container.sh` 会自动 sed 成 `/opt/hermes`。**不要**直接写 `/opt/hermes` —— 会破坏 host 模式回归。
4. **Mac docker desktop 默认内存 2GB**，build 上游镜像会 OOM。`Settings → Resources` 调到 4GB+ 再 build。
