# Awaken MVP

AI 生涯成长产品 MVP。核心角色「小海」通过苏格拉底式对话帮助高中生探索兴趣与职业方向，并把对话沉淀为「今天就能完成」的微行动任务打卡。

## Service Role
- Type: 全栈单体 MVP（`backend` = FastAPI API 服务 + `frontend` = React/Vite SPA）
- Owns: 学生注册/邮箱登录（JWT）、任务生命周期、打卡、对话编排（含 mock 降级）、通知（邮件 / 飞书）
- Does not own: 大模型推理与联网搜索（由外部 DeerFlow 引擎负责，见下文）
- Primary upstreams: 前端 SPA（浏览器）
- Primary downstreams: DeerFlow 2.0 对话引擎（LangGraph，`:8001`）、QQ SMTP、飞书 Webhook

## Service Identity
- PSM: Not applicable（非字节 RPC/PSM 体系，独立部署的 FastAPI 服务）
- HTTP IDL: Not applicable（无 thrift/IDL，接口契约见 [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) 与 FastAPI `/docs`）
- RPC IDL: Not applicable
- 对外契约来源：FastAPI 自动生成的 OpenAPI（`http://localhost:8000/docs`）

## 边界须知（重要）
- `deer-flow/` 是独立 clone 的外部引擎，已被 [.gitignore](file:///Users/bytedance/Awake/.gitignore) 排除，**不属于本版本库**。不要在本仓库为 deer-flow 写代码或改配置；它有自己的 AGENTS.md。
- 本仓库真正的可改代码只有 `backend/` 和 `frontend/`。

## 鉴权现状（重要，必读）
- **已有**：JWT 签发/校验工具 [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py)、`POST /api/login`（邮箱→token）、`GET /api/auth/me`（需 Bearer）、前端 axios 拦截器自动带 Authorization、`localStorage` 会话存储、`/login` 页面、Chat 页 token 会话恢复。
- **未完成**：业务接口（`/api/chat`、`/api/chat/extract-task`、`/api/tasks`、`/api/task-complete`、`/api/students/{email}`、`/api/tasks/{id}`）**当前都没有** `Depends(get_current_student)`，仍可用任意 email 直接访问，前端默认也带 token 但后端未校验。详见 [.agent/rules.md](file:///Users/bytedance/Awake/.agent/rules.md) "Known Pitfalls"。
- 邮件链接 `/chat?email=...` 仍可用，作为"旧链路兼容"入口；无 email 参数时 Chat 页会尝试用 token 恢复会话。

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
- 配置 / 环境变量 / JWT / 小海 prompt：[backend/app/core/config.py](file:///Users/bytedance/Awake/backend/app/core/config.py)
- JWT 工具：[backend/app/services/auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py)
- 数据模型（ORM）：[backend/app/models/models.py](file:///Users/bytedance/Awake/backend/app/models/models.py)
- 请求/响应契约：[backend/app/schemas/schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py)
- DeerFlow 对话适配 & mock 降级：[backend/app/services/deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py)
- 前端路由表：[frontend/src/App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx)
- 前端 API 客户端 + token 拦截器：[frontend/src/api/client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js)

## Interface Inventory
| Capability | Contract/definition | Implementation entry | Test entry | Common change path |
| --- | --- | --- | --- | --- |
| 注册学生 | `POST /api/register` · [schemas.py:19-22](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L19-L22) | [routes.py:63-113](file:///Users/bytedance/Awake/backend/app/api/routes.py#L63-L113) | [test_api.py:TestRegisterAPI](file:///Users/bytedance/Awake/backend/tests/test_api.py) | 改字段→models+schemas+routes |
| 邮箱登录（JWT） | `POST /api/login` · [schemas.py:25-27](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L25-L27) | [routes.py:116-139](file:///Users/bytedance/Awake/backend/app/api/routes.py#L116-L139) | `TestAuthAPI::test_login_*` | 无密码，仅邮箱存在即签发 |
| 当前用户 | `GET /api/auth/me` · Bearer JWT | [routes.py:142-144](file:///Users/bytedance/Awake/backend/app/api/routes.py#L142-L144) + [get_current_student:35-60](file:///Users/bytedance/Awake/backend/app/api/routes.py#L35-L60) | `TestAuthAPI::test_auth_me_*` | 唯一真正校验 token 的接口 |
| 创建任务 | `POST /api/tasks` | [routes.py:147-189](file:///Users/bytedance/Awake/backend/app/api/routes.py#L147-L189) | `TestTaskAPI` | 见 add-field playbook |
| 任务打卡 | `POST /api/task-complete`（幂等） | [routes.py:192-241](file:///Users/bytedance/Awake/backend/app/api/routes.py#L192-L241) | `TestTaskCompleteAPI` | 幂等分支 [routes.py:204-211](file:///Users/bytedance/Awake/backend/app/api/routes.py#L204-L211) |
| 查询学生（含任务） | `GET /api/students/{email}`（未鉴权！） | [routes.py:244-252](file:///Users/bytedance/Awake/backend/app/api/routes.py#L244-L252) | `TestStudentAPI` | — |
| 查询任务 | `GET /api/tasks/{task_id}`（未鉴权！） | [routes.py:255-263](file:///Users/bytedance/Awake/backend/app/api/routes.py#L255-L263) | — | — |
| 多轮对话（小海） | `POST /api/chat`（未鉴权！） | [routes.py:266-279](file:///Users/bytedance/Awake/backend/app/api/routes.py#L266-L279) → [deerflow_service.chat](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L104-L123) | `TestChatAPI` | 见 change-chat-behavior playbook |
| 对话提炼任务 | `POST /api/chat/extract-task`（未鉴权！） | [routes.py:282-320](file:///Users/bytedance/Awake/backend/app/api/routes.py#L282-L320) → [extract_task](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L147-L167) | `TestExtractTaskAPI` | — |
| 健康检查 | `GET /api/health` | [routes.py:323-325](file:///Users/bytedance/Awake/backend/app/api/routes.py#L323-L325) | `TestHealthCheck` | — |
| 前端路由 | `/ /register /login /success /chat /checkin /checkin/demo` | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | — | 加页面→pages+App.jsx |

## Hard Rules
- **Must** 配置与代码分离：所有可变项走 [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) + `.env`，严禁硬编码密钥、URL、端口、阈值、prompt。
- **Must** 保持对话链路永不抛异常：DeerFlow 不可达时必须降级到 mock（[deerflow_service.py:119-123](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L119-L123)）。
- **Must** 前端内页（Chat/CheckIn/Success/Login）使用 `<Navbar variant="app" />`；**例外**：Login.jsx 当前使用默认 `variant="marketing"`（历史遗留，见 Known Pitfalls，改时一并修正）。
- **Must** 保持「探索期 vs 解锁期」两段 prompt 互斥，阈值 `XIAOHAI_UNLOCK_AFTER_TURNS` 与 [routes.py:272](file:///Users/bytedance/Awake/backend/app/api/routes.py#L272) 的 `can_extract_task` 保持一致。
- **Must not** 在本仓库修改 `deer-flow/`（外部依赖，已 gitignore）。
- **Must not** 假设 DeerFlow 是 OpenAI 兼容接口——它是 LangGraph 的 `POST /api/runs/wait`。
- **Must not** 在没有补完鉴权之前写入敏感个人信息（详见 rules.md Security）。
- **Prefer** ponytail / YAGNI：最小改动，不做超出当前 MVP 需求的抽象。

## Proposal To Code
| Requirement type | Start here | Then check | Compatibility | Verify |
| --- | --- | --- | --- | --- |
| 学生/任务加字段 | [models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) | schemas + routes + (可选)前端页面 | SQLite 无迁移，删旧 `awaken.db` 或手动 ALTER | `pytest` |
| 加/改 HTTP 接口 | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | schemas + [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) | 是否需要加 `Depends(get_current_student)`？ | `pytest` + 前端联调 |
| 补完业务接口鉴权 | [routes.py:35-60](file:///Users/bytedance/Awake/backend/app/api/routes.py#L35-L60) `get_current_student` | 逐个接口加 Depends；前端拦截器已就位 | 邮件链接 /chat?email= 无需 token 仍能进（要决策是否保留）| `pytest` + 手动链路 |
| 改小海对话行为 | [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) XIAOHAI_* prompt | deerflow_service；阈值同步 | mock 脚本同步语气 | 手动对话 + `pytest` |
| 改超时 | [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) / [client.js:83-90](file:///Users/bytedance/Awake/frontend/src/api/client.js#L80-L90) / [vite.config.js](file:///Users/bytedance/Awake/frontend/vite.config.js) | 三处链路超时需一致（前端 130s ≥ Vite proxy 130s ≥ 后端 httpx 120s） | — | 长对话实测 |
| 加前端页面/路由 | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | pages/ + Navbar variant | 内页用 `variant="app"` | `npm run build` |

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
```
