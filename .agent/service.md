# Service: Awaken MVP

本文件描述 Awaken MVP 整体的服务边界。整个仓库是一个**单进程 API 服务 + 单进程前端 SPA** 的本地开发形态，生产部署形态 `Needs verification`。

## Identity
- 服务名：Awaken（Awaken AI 生涯成长产品 MVP）
- PSM：Not applicable（独立 FastAPI 应用，无字节 PSM 体系）
- HTTP 端口：后端 `8000`（uvicorn，见 [main.py:44-48](file:///Users/bytedance/Awake/backend/main.py#L44-L48)），前端开发服务器 `3000`（Vite，见 [vite.config.js:7](file:///Users/bytedance/Awake/frontend/vite.config.js#L7)）
- OpenAPI：`http://localhost:8000/docs`（FastAPI 自动生成）
- 代码生成：无（无 thrift/proto/IDL 生成代码）

## Boundary
- **Owns**
  - 学生账号（邮箱维度）注册、邮箱登录、JWT 签发/校验
  - 微行动任务（Task）创建、查询、打卡状态机
  - 「小海」对话编排：system prompt 组装、阶段切换（探索期/解锁期）、多轮消息透传、回复解析
  - 对话→任务提炼的触发时机（前端 `can_extract_task` → 后端轮次判断）
  - 对外通知：注册欢迎邮件（SMTP）、注册/任务飞书 Webhook 卡片
  - 前端 SPA 的全部页面、导航变体、样式、交互、登录态 localStorage 管理
- **Does not own**
  - 大模型推理、联网搜索、Agent 工具链：由外部 DeerFlow 引擎（本地 `:8001`，`deer-flow/` 目录，独立仓库）负责
  - 密码/多因素认证（当前登录仅验证邮箱存在性，无密码）
  - 任务过期调度（`EXPIRED` 状态已定义但无 cron 推进，`Needs verification` 是否有外部触发）
  - 持久化迁移（SQLite 直接 `create_all`，无 Alembic）
  - **业务接口鉴权（半成品）**：JWT 设施已就位，但 `/api/chat`、`/api/chat/extract-task`、`/api/tasks`、`/api/task-complete`、`/api/students/{email}`、`/api/tasks/{id}` 目前未挂 `Depends(get_current_student)`，任意 email 可访问（见 Known Pitfalls）
- **产品需求应落在本仓库**
  - 改小海人设、对话阶段规则、对话交互样式
  - 改学生/任务字段、页面流程、打卡体验
  - 补完业务接口鉴权、加密码/验证码
  - 改通知模板、飞书卡片
- **产品需求应落在 deer-flow/（外部）**
  - 加 LLM 模型、换底层 Agent 框架、加/禁用工具、改记忆/检索后端

## Capabilities
| Capability | Description | Entry | Core modules |
| --- | --- | --- | --- |
| 学生注册 | 邮箱+姓名+年级注册，写库，触发邮件+飞书通知 | `POST /api/register` | [routes.py:63-113](file:///Users/bytedance/Awake/backend/app/api/routes.py#L63-L113), [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py), [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) |
| 邮箱登录（JWT） | 仅校验邮箱存在，签发 7 天 Bearer token | `POST /api/login` | [routes.py:116-139](file:///Users/bytedance/Awake/backend/app/api/routes.py#L116-L139), [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) |
| 当前会话查询 | 校验 JWT，返回当前学生 | `GET /api/auth/me` | [routes.py:142-144](file:///Users/bytedance/Awake/backend/app/api/routes.py#L142-L144), [get_current_student:35-60](file:///Users/bytedance/Awake/backend/app/api/routes.py#L35-L60) |
| 任务创建/查询 | 手动或从对话提炼创建任务 | `POST /api/tasks`, `GET /api/tasks/{id}` | [routes.py:147-189](file:///Users/bytedance/Awake/backend/app/api/routes.py#L147-L189), [routes.py:255-263](file:///Users/bytedance/Awake/backend/app/api/routes.py#L255-L263) |
| 任务打卡 | 幂等完成任务，写反馈，推飞书 | `POST /api/task-complete` | [routes.py:192-241](file:///Users/bytedance/Awake/backend/app/api/routes.py#L192-L241) |
| 学生画像查询 | 返回学生信息+任务列表 | `GET /api/students/{email}` | [routes.py:244-252](file:///Users/bytedance/Awake/backend/app/api/routes.py#L244-L252) |
| 苏格拉底对话 | 透传多轮消息给 DeerFlow/mock，按轮次切换小海阶段 | `POST /api/chat` | [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) |
| 对话提炼任务 | 让 DeerFlow 生成 ≤40 字微行动描述并落库 | `POST /api/chat/extract-task` | [routes.py:282-320](file:///Users/bytedance/Awake/backend/app/api/routes.py#L282-L320) |
| 健康检查 | 存活探针 | `GET /api/health` | [routes.py:323-325](file:///Users/bytedance/Awake/backend/app/api/routes.py#L323-L325) |

## Interfaces
| Interface | Business meaning | Entry | Compatibility notes |
| --- | --- | --- | --- |
| HTTP REST `/api/*` | 前端 SPA 唯一后端 | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | 契约以 Pydantic schema 为准；`ApiResponse` 包装写操作；`/auth/me` 要求 Bearer；其余业务接口当前未校验 token |
| JWT | 登录态 | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | HS256；默认密钥"awaken-dev-secret-change-me"，生产必须通过 `AUTH_SECRET_KEY` 覆盖；有效期 7 天 |
| SMTP（QQ 邮箱 SSL:465） | 注册欢迎邮件 | [email_service.py:21-86](file:///Users/bytedance/Awake/backend/app/services/email_service.py#L21-L86) | 关闭时 `logger.info` mock，不抛异常；邮件 CTA 用 `FRONTEND_URL/chat?email=...` |
| 飞书自定义机器人 Webhook | 注册/打卡/任务卡片通知 | [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) | `FEISHU_ENABLED=false` 时仅打日志；任务卡片 `notify_task_created` 当前始终走 logger（未实际 POST webhook，`Needs verification` 是否为预期） |
| DeerFlow LangGraph API | 对话推理 | `POST {DEERFLOW_BASE_URL}/api/runs/wait`（[deerflow_service.py:51-66](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L51-L66)）| 非 OpenAI 兼容；超时 120s；thread_id 用随机 uuid（无状态）；失败自动降级 mock |

## Interface Inventory
| Capability type | Business meaning | Definition entry | Implementation entry | Test entry | Common change path |
| --- | --- | --- | --- | --- | --- |
| HTTP | 注册 | [schemas.py:19-22](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L19-L22) | [routes.py:63](file:///Users/bytedance/Awake/backend/app/api/routes.py#L63-L113) | `TestRegisterAPI` | 改字段动 models+schemas+routes |
| HTTP | 登录（JWT） | [schemas.py:25-27](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L25-L27) | [routes.py:116](file:///Users/bytedance/Awake/backend/app/api/routes.py#L116-L139) | `TestAuthAPI::test_login_*` | 加密码/验证码 → auth_service + schema |
| HTTP | 当前会话（需鉴权） | — | [routes.py:142](file:///Users/bytedance/Awake/backend/app/api/routes.py#L142-L144) | `TestAuthAPI::test_auth_me_*` | 补鉴权时以本接口为参考样板 |
| HTTP | 创建任务 | [schemas.py:41-44](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L41-L44) | [routes.py:147](file:///Users/bytedance/Awake/backend/app/api/routes.py#L147-L189) | `TestTaskAPI` | — |
| HTTP | 任务打卡（幂等） | [schemas.py:47-49](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L47-L49) | [routes.py:192](file:///Users/bytedance/Awake/backend/app/api/routes.py#L192-L241) | `TestTaskCompleteAPI` | 幂等分支必须保留 |
| HTTP | 查询学生 | URL path | [routes.py:244](file:///Users/bytedance/Awake/backend/app/api/routes.py#L244-L252) | `TestStudentAPI` | 未鉴权（待补） |
| HTTP | 对话 | [schemas.py:82-91](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L82-L91) | [deerflow_service.py:104](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L104-L123) | `TestChatAPI` | 改 prompt 动 config.py；未鉴权（待补） |
| HTTP | 对话提炼任务 | [schemas.py:94-96](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L94-L96) | [deerflow_service.py:147](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L147-L167) | `TestExtractTaskAPI` | 未鉴权（待补） |
| Frontend route | 营销落地 | `/` → Landing | [App.jsx:13](file:///Users/bytedance/Awake/frontend/src/App.jsx#L13) | — | 内页禁止复用 marketing 导航 |
| Frontend route | 注册 | `/register` → Register | [App.jsx:14](file:///Users/bytedance/Awake/frontend/src/App.jsx#L14) | — | — |
| Frontend route | 登录 | `/login` → Login | [App.jsx:15](file:///Users/bytedance/Awake/frontend/src/App.jsx#L15) | — | Login.jsx 当前使用默认 marketing variant（待修正） |
| Frontend route | 注册成功 | `/success` → Success | [App.jsx:16](file:///Users/bytedance/Awake/frontend/src/App.jsx#L16) | — | 提供带 `?email=` 的直达按钮 |
| Frontend route | 对话 | `/chat`（`?email=...` 可选）→ Chat | [App.jsx:17](file:///Users/bytedance/Awake/frontend/src/App.jsx#L17) | — | 无 email 时走 token 恢复→失败引导登录 |
| Frontend route | 打卡 | `/checkin?task_id=...` → CheckIn；`/checkin/demo?email=...` 演示模式 | [App.jsx:18-19](file:///Users/bytedance/Awake/frontend/src/App.jsx#L18-L19) | — | — |

## Data And Dependencies
| Resource | Usage | Code location | Failure/compatibility notes |
| --- | --- | --- | --- |
| SQLite | 持久化学生与任务 | [database.py](file:///Users/bytedance/Awake/backend/app/core/database.py), `DATABASE_URL` in [config.py:10](file:///Users/bytedance/Awake/backend/app/core/config.py#L10) | `awaken.db` 在 backend 根目录（已 gitignore）；无迁移框架；测试走独立 `test_awaken.db` |
| JWT (jose) | 登录态签发/校验 | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | 密钥从 `AUTH_SECRET_KEY`；默认值仅用于本地开发 |
| DeerFlow（外部） | 对话推理 | `DEERFLOW_BASE_URL` 默认 `http://localhost:8001` | 120s 超时；失败→mock 降级；需配合 DeerFlow 的 `DEER_FLOW_AUTH_DISABLED=1` 本地启动 |
| QQ SMTP | 欢迎邮件 | [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) | 非必需，`SMTP_ENABLED=false` 走 mock 日志 |
| 飞书 Webhook | 注册/打卡/任务通知 | [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) | Webhook 地址走 `.env`；失败不影响主流程；task_created 当前只打日志 |
| localStorage | 前端 token 与学生信息缓存 | [client.js:11-35](file:///Users/bytedance/Awake/frontend/src/api/client.js#L11-L35) | key: `awaken_access_token` / `awaken_student`；axios 拦截器自动带 Authorization（[client.js:37-43](file:///Users/bytedance/Awake/frontend/src/api/client.js#L37-L43)）|
| 前端 Vite proxy | 开发态把 `/api` 代理到 `:8000` | [vite.config.js:8-16](file:///Users/bytedance/Awake/frontend/vite.config.js#L8-L16) | `timeout/proxyTimeout` 130s > 后端 120s |

## Configuration
| Config | Purpose | Code location | Risk |
| --- | --- | --- | --- |
| `APP_ENV` / `DEBUG` | 日志级别与 uvicorn reload | [config.py:8-9](file:///Users/bytedance/Awake/backend/app/core/config.py#L8-L9), [main.py:44-48](file:///Users/bytedance/Awake/backend/main.py#L44-L48) | 生产必须 `DEBUG=false` |
| `DATABASE_URL` | SQLite 路径 | [config.py:10](file:///Users/bytedance/Awake/backend/app/core/config.py#L10) | 切换到 Postgres 需改 connect_args 与 driver |
| `AUTH_SECRET_KEY` / `AUTH_ALGORITHM` / `AUTH_TOKEN_EXPIRE_MINUTES` | JWT | [config.py:11-13](file:///Users/bytedance/Awake/backend/app/core/config.py#L11-L13) | **生产必须替换默认密钥**；默认值仅限本地 |
| `SMTP_*` / `SMTP_ENABLED` | 邮件 | [config.py:15-20](file:///Users/bytedance/Awake/backend/app/core/config.py#L15-L20) | 密码是 QQ 邮箱授权码，非登录密码 |
| `FEISHU_*` / `FEISHU_ENABLED` | 飞书通知 | [config.py:22-24](file:///Users/bytedance/Awake/backend/app/core/config.py#L22-L24) | 关闭时日志 mock |
| `DEERFLOW_*` | DeerFlow 连接 | [config.py:26-32](file:///Users/bytedance/Awake/backend/app/core/config.py#L26-L32) | 本地开发需 `DEER_FLOW_AUTH_DISABLED=1` 在 deer-flow 侧 |
| `XIAOHAI_*_PROMPT` / `XIAOHAI_UNLOCK_AFTER_TURNS` | 小海人设与阶段规则 | [config.py:34-55](file:///Users/bytedance/Awake/backend/app/core/config.py#L34-L55) | 阈值必须与 `can_extract_task` 一致 |
| `FRONTEND_URL` | 邮件 CTA、飞书卡片跳转 | [config.py:57](file:///Users/bytedance/Awake/backend/app/core/config.py#L57) | 部署后必须改 |
| `BACKEND_CORS_ORIGINS` | 允许的前端 Origin | [config.py:58-69](file:///Users/bytedance/Awake/backend/app/core/config.py#L58-L69) | 部署域名必须加入 |

## Change Ownership
| Requirement type | Preferred landing service/module | Reason |
| --- | --- | --- |
| 改人设/对话阶段/回复语气 | [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) 中 `XIAOHAI_*_PROMPT`，必要时 [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | prompt 是单一事实源 |
| 补完接口鉴权 | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) 中逐个加 `Depends(get_current_student)`；必要时改 student_email 从 token 取而非请求体 | `get_current_student` 已有参考样板；前端拦截器已就位 |
| 加密码/验证码 | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) + models.py（加 password hash 字段）+ schema | 当前登录无密码，属安全提升 |
| 改数据字段 | [models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) + [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) + 对应路由 | ORM/Schema/API 三点齐改 |
| 改导航显示逻辑 | [Navbar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Navbar.jsx) `variant` 分支 | 营销页与 App 页已通过 variant 隔离 |
| 改聊天 UI 样式 | [Chat.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Chat.jsx) + [global.css](file:///Users/bytedance/Awake/frontend/src/styles/global.css) | — |
| 加通知渠道 | 新增 service 文件并在对应路由处调用，遵循现有 email/feishu 的 **失败不抛、仅记日志** 约定 | 通知是 best-effort，不能阻塞注册/打卡 |
| 换 LLM/加工具/改记忆后端 | 外部 `deer-flow/` 仓库 | 本仓库只调 HTTP API |
