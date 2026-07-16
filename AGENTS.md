# Awaken MVP

AI 生涯成长产品 MVP。核心角色「小海」通过苏格拉底式对话帮助高中生探索兴趣与职业方向，并把对话沉淀为「今天就能完成」的微行动任务打卡。

## Service Role
- Type: 全栈单体 MVP（`backend` = FastAPI API 服务 + `frontend` = React/Vite SPA）
- Owns: 学生注册/邮箱+密码登录（JWT）、密码哈希（PBKDF2_SHA256）、任务生命周期、打卡、对话编排（含 mock 降级）、DeerFlow 能力控制面板（skills 开关/模型列表/状态）、通知（邮件 / 飞书）
- Does not own: 大模型推理与联网搜索（由外部 DeerFlow 引擎负责，见下文）
- Primary upstreams: 前端 SPA（浏览器）
- Primary downstreams: DeerFlow 2.0 对话引擎（LangGraph，`:8001`，含对话 + 控制接口）、QQ SMTP、飞书 Webhook
- 部署形态: Docker 化（backend Python:3.11-slim + frontend nginx:1.27-alpine 多阶段构建）

## Service Identity
- PSM: Not applicable（非字节 RPC/PSM 体系，独立部署的 FastAPI 服务）
- HTTP IDL: Not applicable（无 thrift/IDL，接口契约见 [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) 与 FastAPI `/docs`）
- RPC IDL: Not applicable
- 对外契约来源：FastAPI 自动生成的 OpenAPI（`http://localhost:8000/docs`）

## 边界须知（重要）
- `deer-flow/` 是独立 clone 的外部引擎，已被 [.gitignore](file:///Users/bytedance/Awake/.gitignore) 排除，**不属于本版本库**。不要在本仓库为 deer-flow 写代码或改配置；它有自己的 AGENTS.md。
- 本仓库真正的可改代码只有 `backend/` 和 `frontend/`。
- 前端 Workspace 架构：[WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) 承载 Sidebar + ContextBar + Outlet 子路由，是 `/app/*` 所有功能页的外壳。

## 鉴权现状（重要，必读）
- **已有**：
  - PBKDF2_SHA256 密码哈希（[auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py)，260k 迭代，16 字节盐）
  - JWT 签发/校验工具
  - `POST /api/register`（邮箱+密码，min_length=8）
  - `POST /api/login`（邮箱+密码→token，验密码哈希）
  - `GET /api/auth/me` 及学生业务接口均需 Bearer，并按 token 中的学生身份校验资源归属
  - DeerFlow 控制接口要求有效学生 token，但普通学生固定返回 403；控制 UI 仅保留作内部联调代码
  - 前端 axios 拦截器自动带 Authorization、`localStorage` 会话存储
  - 旧用户密码迁移：[migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py) 在 `init_db` 时对 `password_hash` 为空的行用 `AUTH_LEGACY_USER_DEFAULT_PASSWORD` 回填
- 邮件链接 `/chat?email=...` 仍会重定向到 `/app/chat?email=...`，但 email 只用于兼容导航，不能代替 token 或访问其他学生数据。

## Read First
- 服务边界与能力：[.agent/service.md](file:///Users/bytedance/Awake/.agent/service.md)
- 代码地图 / 关键词路由：[.agent/indexes/code_index.md](file:///Users/bytedance/Awake/.agent/indexes/code_index.md)
- 架构规则与红线：[.agent/rules.md](file:///Users/bytedance/Awake/.agent/rules.md)
- 架构决策记录：[.agent/decisions/architecture-decisions.md](file:///Users/bytedance/Awake/.agent/decisions/architecture-decisions.md)
- 变更手册：[加字段](file:///Users/bytedance/Awake/.agent/playbooks/add-field.md)、[加接口](file:///Users/bytedance/Awake/.agent/playbooks/add-api-endpoint.md)、[改对话行为](file:///Users/bytedance/Awake/.agent/playbooks/change-chat-behavior.md)
- 产品/技术方案原稿：[docs/](file:///Users/bytedance/Awake/docs)

## Code Entry Points
- 后端启动 & CORS：[backend/main.py](file:///Users/bytedance/Awake/backend/main.py)
- 所有 HTTP 路由 + 鉴权依赖：[backend/app/api/routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py)
- 配置 / 环境变量 / JWT / 小海 prompt / DeerFlow 控制超时：[backend/app/core/config.py](file:///Users/bytedance/Awake/backend/app/core/config.py)
- JWT + PBKDF2 密码哈希工具：[backend/app/services/auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py)
- 数据模型（ORM，含 password_hash）：[backend/app/models/models.py](file:///Users/bytedance/Awake/backend/app/models/models.py)
- 请求/响应契约（含 DeerFlow* schemas）：[backend/app/schemas/schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py)
- DeerFlow 对话适配 & mock 降级：[backend/app/services/deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py)
- DeerFlow 控制面板代理（status/skills/toggle/models）：[backend/app/services/deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py)
- SQLite 旧库迁移（密码哈希回填）：[backend/app/core/migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py)
- DB 初始化（含迁移调用）：[backend/app/core/database.py](file:///Users/bytedance/Awake/backend/app/core/database.py)
- 前端路由表（/app 子路由 + 重定向）：[frontend/src/App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx)
- 前端 Workspace 外壳（Sidebar + ContextBar + Outlet）：[frontend/src/layouts/WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx)
- 前端 API 客户端 + token 拦截器 + DeerFlow 控制 API：[frontend/src/api/client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js)

## Interface Inventory
| Capability | Contract/definition | Implementation entry | Test entry | Common change path |
| --- | --- | --- | --- | --- |
| 注册学生（含密码） | `POST /api/register` · [schemas.py:19-23](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L19-L23) | [routes.py:70-121](file:///Users/bytedance/Awake/backend/app/api/routes.py#L70-L121) | [test_api.py:TestRegisterAPI](file:///Users/bytedance/Awake/backend/tests/test_api.py) | 密码→auth_service.hash_password |
| 邮箱+密码登录（JWT） | `POST /api/login` · [schemas.py:26-28](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L26-L28) | [routes.py:124-152](file:///Users/bytedance/Awake/backend/app/api/routes.py#L124-L152) | `TestAuthAPI::test_login_*` | verify_password 验哈希 |
| 当前用户 | `GET /api/auth/me` · Bearer JWT | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) `get_current_student` | `TestAuthAPI::test_auth_me_*` | 业务接口共用鉴权依赖 |
| 创建任务 | `POST /api/tasks`（需鉴权） | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | `TestTaskAPI` | 学生身份取自 token |
| 任务打卡 | `POST /api/task-complete`（需鉴权、幂等） | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | `TestTaskCompleteAPI` | 校验任务归属 |
| 查询学生（含任务） | `GET /api/students/{email}`（需鉴权） | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | `TestStudentAPI` | email 必须与当前学生一致 |
| 查询任务 | `GET /api/tasks/{task_id}`（需鉴权） | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | `test_authorization.py` | 校验任务归属 |
| 多轮对话（小海） | `POST /api/chat`（需鉴权） | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) → [deerflow_service.chat](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | `TestChatAPI` | 历史按当前学生持久化 |
| 对话提炼任务 | `POST /api/chat/extract-task`（需鉴权） | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) → [extract_task](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | `TestExtractTaskAPI` | 返回结构化微行动 |
| DeerFlow 控制接口 | `/api/deerflow/*`（学生禁止） | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) `deny_student_control_access` | `test_deerflow_control.py` | 有效学生 token 返回 403 |
| 健康检查 | `GET /api/health` | [routes.py:389-391](file:///Users/bytedance/Awake/backend/app/api/routes.py#L389-L391) | `TestHealthCheck` | Docker HEALTHCHECK 调此接口 |
| 前端营销路由 | `/ /register /login /success /checkin /checkin/demo` | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | — | 这些页面在 WorkspaceLayout 外 |
| 前端 Workspace 路由 | `/app/today /app/chat /app/tasks /app/focus /app/checkin /app/explore /app/growth /app/settings` | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) → [WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) | — | `/app/capabilities` 重定向到今日页 |
| 旧路径兼容 | `/chat` → `/app/chat`（302） | [App.jsx:15-18](file:///Users/bytedance/Awake/frontend/src/App.jsx#L15-L18) | — | 保留 query string |

## Hard Rules
- **Must** 配置与代码分离：所有可变项走 [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) + `.env`，严禁硬编码密钥、URL、端口、阈值、prompt。
- **Must** 保持对话链路永不抛异常：DeerFlow 不可达时必须降级到 mock（[deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py)）；DeerFlow 控制接口不可达时必须返回 online=false 降级态（不抛 500）。
- **Must** 所有 `/app/*` 功能页使用 `<WorkspaceLayout>` 外壳（内含 Sidebar + ContextBar）；Landing 使用 marketing Navbar，Register/Login/Success 使用 app Navbar。
- **Must** 保持「探索期 vs 解锁期」两段 prompt 互斥，阈值 `XIAOHAI_UNLOCK_AFTER_TURNS` 与 [routes.py:285](file:///Users/bytedance/Awake/backend/app/api/routes.py#L285) 的 `can_extract_task = user_turns >= 3` 保持一致。
- **Must not** 在本仓库修改 `deer-flow/`（外部依赖，已 gitignore）。
- **Must not** 假设 DeerFlow 是 OpenAI 兼容接口——对话走 LangGraph 的 `POST /api/runs/wait`；控制接口走 `/api/models`、`/api/skills`、`PUT /api/skills/{name}`。
- **Must not** 信任请求体或 URL 中的学生身份；资源归属必须以 Bearer token 解析出的当前学生为准。
- **Must not** 引入状态管理库（Redux/Zustand）或 UI 组件库（AntD/MUI），保持零额外依赖手写组件（当前 frontend 仅 react + react-router-dom + axios）。
- **Prefer** ponytail / YAGNI：最小改动，不做超出当前 MVP 需求的抽象。

## Docker
- Backend: [backend/Dockerfile](file:///Users/bytedance/Awake/backend/Dockerfile) — python:3.11-slim，端口 8000，HEALTHCHECK 调 `/api/health`
- Frontend: [frontend/Dockerfile](file:///Users/bytedance/Awake/frontend/Dockerfile) + [frontend/nginx.conf](file:///Users/bytedance/Awake/frontend/nginx.conf) — 多阶段构建 node:20-alpine → nginx:1.27-alpine，SPA fallback + `/api/` 反向代理到 backend:8000，proxy_read_timeout 130s

## Proposal To Code
| Requirement type | Start here | Then check | Compatibility | Verify |
| --- | --- | --- | --- | --- |
| 学生/任务加字段 | [models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) | schemas + routes + (可选)前端页面 | SQLite 无自动迁移；已有字段用 ALTER（见 [migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py) 模式）或删旧 `awaken.db` | `pytest` |
| 加/改 HTTP 接口 | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | schemas + [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) | 新接口默认应当加 `Depends(get_current_student)` | `pytest` + 前端联调 |
| 改业务接口鉴权 | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) `get_current_student` | 保持资源归属校验；前端拦截器已就位 | email 查询参数不得越过 token 身份；控制接口保持学生 403 | `pytest` + 手动链路 |
| 改密码策略 | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) `hash_password/verify_password` | config.py（迭代次数/算法）+ migrations.py | 旧密码用 `AUTH_LEGACY_USER_DEFAULT_PASSWORD` 回填，改默认密码需先跑迁移脚本 | `pytest`（含 TestPasswordHashing + TestPasswordMigration） |
| 改小海对话行为 | [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) XIAOHAI_* prompt | deerflow_service；阈值同步 | mock 脚本同步语气 | 手动对话 + `pytest` |
| 改 DeerFlow skill/model | 前端 [Capabilities.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Capabilities.jsx) → 后端 [deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) → DeerFlow `/api/skills` | 归一化函数 `_normalize_skills/_normalize_models` | 离线时前端降级只读 | `pytest tests/test_deerflow_control.py` + 前端联调 |
| 改超时 | [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py)（httpx 120s + DEERFLOW_CONTROL_TIMEOUT_SECONDS 60s）/ [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js)（chat 130s / control 60s）/ [vite.config.js](file:///Users/bytedance/Awake/frontend/vite.config.js)（130s）/ [nginx.conf](file:///Users/bytedance/Awake/frontend/nginx.conf)（130s） | 四处链路超时需一致：前端 chat 130s ≥ Vite/nginx proxy 130s ≥ 后端 httpx 120s；control 接口 60s 独立 | — | 长对话实测 |
| 加 Workspace 内页/路由 | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) `/app` 子路由 | pages/ + [Sidebar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Sidebar.jsx) 导航项 + [ContextBar.jsx](file:///Users/bytedance/Awake/frontend/src/components/ContextBar.jsx) SECTION_TITLES | 内页使用 WorkspaceLayout 外壳（自动包含 Sidebar/ContextBar） | `npm run build` |
| 加非 Workspace 页面 | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) 顶层路由 | pages/ + Navbar variant | 营销/落地→默认 marketing；功能页→`variant="app"` | `npm run build` |

## Verify
```bash
# 后端单测（自动隔离 SMTP/DeerFlow，走 mock；默认 JWT 密钥为 "awaken-dev-secret-change-me"）
cd backend && pytest

# 前端构建
cd frontend && npm run build

# 本地全链路（三个进程）
cd deer-flow && DEER_FLOW_AUTH_DISABLED=1 <deerflow 启动命令>   # :8001，外部仓库
cd backend && uvicorn main:app --reload --port 8000            # :8000
cd frontend && npm run dev                                     # :3000（proxy /api → :8000）

# Docker 构建（可选）
cd backend && docker build -t awaken-backend .
cd frontend && docker build -t awaken-frontend .
```
