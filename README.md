# Awaken MVP

Awaken 是一个 AI 生涯成长产品 MVP。核心角色「小海」通过苏格拉底式对话帮助高中生探索兴趣与职业方向，并把对话沉淀为今天就能完成的微行动任务。

## 项目结构

```text
.
├── backend/              # FastAPI API 服务、SQLite 数据模型、对话编排
├── frontend/             # React + Vite 单页应用
├── docs/                 # 产品与技术方案文档
├── docker-compose.yml    # 本地 Docker 一键启动编排
└── AGENTS.md             # 面向 AI Agent 的项目规则与代码地图
```

`deer-flow/` 是外部独立仓库，不属于本版本库。Awaken 只通过 HTTP 调用本机或外部 DeerFlow 服务；当 DeerFlow 不可用时，后端会降级到 mock 对话。

## 技术栈

- 前端：React 18、Vite、Axios、React Router
- 后端：FastAPI、SQLAlchemy、SQLite、JWT
- 可选下游：DeerFlow 2.0、QQ SMTP、飞书 Webhook
- 容器化：Docker Compose、Nginx、Python 3.11

## Docker 本地启动

确保本机已安装 Docker Desktop 或 Docker Engine，然后在仓库根目录执行：

```bash
docker compose up --build
```

启动后访问：

- 前端应用：`http://localhost:3000`
- 后端 API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:3000/health` 或 `http://localhost:8000/api/health`

默认配置下：

- SQLite 数据保存在 Docker volume `awaken_backend_data` 中。
- `DEERFLOW_ENABLED=false`，对话链路走 mock 降级，适合直接本地体验。
- 前端容器通过 Nginx 将 `/api/*` 反向代理到后端容器。

停止服务：

```bash
docker compose down
```

如果需要同时删除本地容器数据库：

```bash
docker compose down -v
```

## 连接本机 DeerFlow

如果你已经在宿主机启动 DeerFlow，并监听 `8001` 端口，可以这样启动 Awaken：

```bash
DEERFLOW_ENABLED=true \
DEERFLOW_BASE_URL=http://host.docker.internal:8001 \
DEERFLOW_ASSISTANT_ID=lead_agent \
docker compose up --build
```

如果 DeerFlow 开启了鉴权，再额外传入：

```bash
DEERFLOW_API_KEY=your-api-key docker compose up --build
```

## 常用环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `AUTH_SECRET_KEY` | `awaken-dev-secret-change-me` | JWT 签名密钥，本地可用默认值，公开部署必须替换 |
| `DATABASE_URL` | `sqlite:///./data/awaken.db` | Docker 内默认 SQLite 路径 |
| `SMTP_ENABLED` | `false` | 是否启用 QQ SMTP 邮件 |
| `FEISHU_ENABLED` | `false` | 是否启用飞书 Webhook |
| `DEERFLOW_ENABLED` | `false` | 是否启用 DeerFlow 对话引擎 |
| `DEERFLOW_BASE_URL` | `http://host.docker.internal:8001` | Docker 中访问宿主机 DeerFlow 的地址 |
| `FRONTEND_URL` | `http://localhost:3000` | 邮件和跳转链接使用的前端地址 |

更多后端配置参考 `backend/.env.example`。

## 非 Docker 开发

后端：

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

本地开发地址：

- 前端：`http://localhost:3000`
- 后端：`http://localhost:8000`

## 测试与构建

后端单测：

```bash
cd backend
pytest
```

前端构建：

```bash
cd frontend
npm run build
```

Docker 构建与启动验证：

```bash
docker compose config
docker compose up --build
```

## 当前安全边界

项目已有邮箱登录、JWT 签发、`GET /api/auth/me` token 校验和前端 token 拦截器。

仍需注意：部分业务接口仍兼容旧的邮箱参数入口，尚未全部强制 `Depends(get_current_student)`。在公开部署或写入敏感个人信息前，应先补完业务接口鉴权。

## GitHub 发布

当前仓库远端为：

```bash
git remote -v
```

常规发布流程：

```bash
git status --short
git add .
git commit -m "chore: add docker local startup"
git push origin master
```
