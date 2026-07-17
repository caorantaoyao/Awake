# Awaken

AI 生涯成长产品。核心角色「小海」通过对话帮助高中生探索兴趣与职业方向，并把对话沉淀为「今天就能完成」的微行动任务（5–30 分钟）。

## 架构概览

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  React SPA   │ ───► │  FastAPI     │ ───► │  DeerFlow 2.0│
│  (Nginx)     │ /api │  (Awaken)    │ HTTP │  Gateway     │
│  端口 7777   │      │  端口 8000   │ SSE  │  端口 8001   │
└──────────────┘      └──────────────┘      └──────┬───────┘
       │                   │                       │
       ▼                   ▼                       ▼
  静态资源/SPA       SQLite 数据库            Redis (SSE 桥接)
```

- **本仓库**：FastAPI 单体后端 + React/Vite SPA。
- **DeerFlow**：包含在 docker-compose 中作为服务启动（基于 `./deer-flow/` 目录的本地 clone），负责大模型推理、工具调用、记忆、联网搜索。
- **鉴权**：邮箱+密码注册登录（PBKDF2_SHA256 密码哈希），JWT Bearer Token，所有业务接口校验学生身份归属。

## 项目结构

```text
.
├── backend/                  # FastAPI 服务
│   ├── main.py               # 入口 & CORS
│   ├── app/
│   │   ├── api/routes.py     # 全部 HTTP 路由 + 鉴权依赖
│   │   ├── core/             # 配置、数据库、迁移
│   │   ├── models/           # SQLAlchemy ORM（学生、任务、会话、成长事件）
│   │   ├── schemas/          # Pydantic 请求/响应契约
│   │   └── services/         # DeerFlow 适配、鉴权、通知
│   ├── tests/                # pytest（99+ 用例）
│   └── Dockerfile            # python:3.11-slim
├── frontend/                 # React 18 + Vite SPA
│   ├── src/
│   │   ├── pages/            # Chat、Onboarding、Today、Tasks、Capabilities...
│   │   ├── components/       # Sidebar、ContextBar、RequireAuth...
│   │   ├── api/client.js     # Axios 客户端 + token 拦截器
│   │   ├── config/onboarding.js  # 引导步骤配置
│   │   └── styles/global.css # Codex 风格全局样式
│   ├── nginx.conf            # SPA fallback + /api/ 反向代理
│   └── Dockerfile            # 多阶段构建 node:20-alpine → nginx:1.27-alpine
├── docs/                     # 产品与技术方案文档
├── docker-compose.yml        # 本地 Docker 一键启动
└── AGENTS.md                 # 面向 AI Agent 的项目规则与代码地图
```

## 核心功能

| 模块 | 说明 |
|---|---|
| 注册/登录 | 邮箱+密码，JWT，PBKDF2_SHA256（260k 迭代） |
| Onboarding 引导 | 三步式标签选择（兴趣/困惑/学习偏好），结果写入 StudentProfile |
| 对话（Chat） | SSE 流式打字机渲染，支持思考链、计划模式、产出物卡片、Markdown/GFM |
| 会话管理 | 多 Thread CRUD，模型切换，思考/计划模式开关 |
| 微行动任务 | 3 轮对话后可提炼结构化任务；estimated_minutes 强制 5–30 分钟（代码 clamp + DB CheckConstraint） |
| 打卡/成长记录 | 任务打卡、GrowthEvent 时间线、成长摘要 |
| 文件上传 | 对话中上传文件，随消息携带 file_ids |
| 输入润色 | 魔法棒按钮一键润色输入内容 |
| 反馈 | 消息 👍/👎 反馈 |
| 能力控制 | Skills 开关、模型列表、MCP 服务器、Run 历史、定时任务（内部联调用，学生账号 403） |

## 快速开始

### 前置依赖

- Python 3.11+
- Node.js 20+
- DeerFlow 2.0 源码 clone 到 `./deer-flow/` 目录（docker-compose 会自动构建）
- 一个 LLM API Key（默认配置使用 DeepSeek，通过 `DEEPSEEK_API_KEY` 环境变量传入）

### 本地开发

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
npm run dev   # http://localhost:7777
```

访问：

- 前端：http://localhost:7777
- 后端 API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

### Docker Compose（一键启动全栈）

确保 `./deer-flow/` 目录存在（`git clone <deerflow-repo> deer-flow`），然后：

```bash
DEEPSEEK_API_KEY=sk-xxx docker compose up --build
```

compose 将启动 4 个服务：**redis** → **deerflow** (8001) → **backend** (8000) → **frontend** (7777)。

启动后访问：

- 前端：http://localhost:7777
- 后端 API 文档：http://localhost:8000/docs
- DeerFlow API 文档：http://localhost:8001/docs
- 健康检查：http://localhost:7777/health（前端 Nginx）或 http://localhost:8000/api/health

不设置 `DEEPSEEK_API_KEY` 也能启动容器，但对话时 LLM 调用会失败。如需使用其他模型提供商，编辑 `docker/deerflow/config.yaml` 添加模型配置。

停止并清理数据卷：

```bash
docker compose down -v
```

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `AUTH_SECRET_KEY` | `awaken-dev-secret-change-me` | JWT 签名密钥，**公开部署必须替换** |
| `DEEPSEEK_API_KEY` | _(空)_ | DeepSeek API Key（DeerFlow 默认模型），**对话必须** |
| `DATABASE_URL` | `sqlite:///./awaken.db`（本地）/ `sqlite:///./data/awaken.db`（Docker） | 数据库连接 |
| `DEERFLOW_BASE_URL` | `http://localhost:8001`（本地）/ `http://deerflow:8001`（Docker） | DeerFlow 地址 |
| `DEERFLOW_ASSISTANT_ID` | `lead_agent` | DeerFlow assistant ID |
| `DEERFLOW_API_KEY` | _(空)_ | DeerFlow Bearer Token（Docker 中关闭鉴权，无需设置） |
| `DEERFLOW_CONTROL_TIMEOUT_SECONDS` | `60` | DeerFlow 控制接口超时 |
| `SMTP_ENABLED` | `false` | 启用 QQ SMTP 邮件通知 |
| `FEISHU_ENABLED` | `false` | 启用飞书 Webhook 通知 |
| `FRONTEND_URL` | `http://localhost:7777` | 邮件和跳转链接中的前端地址 |
| `XIAOHAI_UNLOCK_AFTER_TURNS` | `3` | 多少轮对话后可提炼微行动 |

## 测试

```bash
cd backend && pytest          # 后端单测（自动隔离 SMTP/DeerFlow）
cd frontend && npm run build  # 前端构建验证
```

## 关键约束（开发必读）

1. **DeerFlow 是核心依赖**：对话链路不做 mock 降级，DeerFlow 不可达时对话返回 503；控制接口（MCP/Runs/ScheduledTasks）优雅降级返回空数据。
2. **资源归属以 token 为准**：不信任请求体中的学生身份，所有接口从 JWT 解析当前学生。
3. **前端零额外 UI 库**：不引入 AntD/MUI/Redux/Zustand，使用原生 React Hooks + 手写 CSS。
4. **微行动时间硬约束**：estimated_minutes 在代码层 clamp(5,30)，数据库层有 CheckConstraint。
5. **提示词修改需新会话**：LangGraph 有 thread 缓存，改 system prompt 后必须新建会话生效。
6. **超时链路一致**：前端 chat 130s ≥ Nginx proxy 130s ≥ 后端 httpx 120s；control 接口独立 60s。
7. **deer-flow/ 目录不纳入版本控制**：Docker 构建时从本地 `./deer-flow/` 目录构建镜像，新环境需先 clone DeerFlow 源码到该目录。

## 技术栈

- **前端**：React 18、Vite 5、React Router v6、Axios、react-markdown、remark-gfm
- **后端**：FastAPI、SQLAlchemy、SQLite、Pydantic v2、PyJWT、httpx
- **容器**：Docker Compose、Nginx 1.27（前端）、Python 3.11-slim（Awaken 后端）、Python 3.12（DeerFlow Gateway）、Redis 7（SSE 桥接）
- **下游**：DeepSeek API（默认 LLM）、QQ SMTP、飞书 Webhook

## License

MIT
