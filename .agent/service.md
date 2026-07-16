# Service: Awaken MVP

本文件描述 Awaken MVP 整体的服务边界。整个仓库是一个**单进程 API 服务 + 单进程前端 SPA** 的本地开发形态，生产部署通过 Docker（backend Python + frontend nginx）。

## Identity
- 服务名：Awaken（Awaken AI 生涯成长产品 MVP）
- PSM：Not applicable（独立 FastAPI 应用，无字节 PSM 体系）
- HTTP 端口：后端 `8000`（uvicorn，见 [main.py](file:///Users/bytedance/Awake/backend/main.py)），前端开发服务器 `3000`（Vite，见 [vite.config.js:7](file:///Users/bytedance/Awake/frontend/vite.config.js#L7)）；Docker 部署时 frontend nginx 暴露 `80`，反向代理 `/api` → backend:8000
- OpenAPI：`http://localhost:8000/docs`（FastAPI 自动生成）
- 代码生成：无（无 thrift/proto/IDL 生成代码）

## Boundary
- **Owns**
  - 学生账号（邮箱维度）注册、邮箱+密码登录（PBKDF2_SHA256）、JWT 签发/校验
  - 旧用户密码迁移（SQLite ALTER TABLE + 默认密码回填）
  - 微行动任务（Task）创建、查询、打卡状态机
  - 「小海」对话编排：system prompt 组装、阶段切换（探索期/解锁期）、多轮消息透传、回复解析
  - 对话→任务提炼的触发时机（前端 `can_extract_task` → 后端轮次判断）
  - DeerFlow 控制面板：代理 DeerFlow gateway 的 status/skills/models 接口，提供 skill 开关，归一化返回，离线降级
  - 对外通知：注册欢迎邮件（SMTP）、注册/任务飞书 Webhook 卡片
  - 前端 SPA 的全部页面、Workspace 布局（Sidebar + ContextBar）、导航变体、样式、交互、登录态 localStorage 管理
  - Docker 化部署（backend Dockerfile + frontend 多阶段 Dockerfile + nginx.conf）
- **Does not own**
  - 大模型推理、联网搜索、Agent 工具链：由外部 DeerFlow 引擎（本地 `:8001`，`deer-flow/` 目录，独立仓库）负责
  - 任务过期调度（`EXPIRED` 状态已定义但无 cron 推进，前端 Tasks 页按 deadline 前端分组）
  - 持久化迁移框架（无 Alembic；通过 [migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py) 做一次性 ALTER + 回填，init_db 时自动执行）
- **产品需求应落在本仓库**
  - 改小海人设、对话阶段规则、对话交互样式
  - 改学生/任务字段、页面流程、打卡体验
  - 补完业务接口鉴权、加强密码策略
  - 改通知模板、飞书卡片
  - 改 DeerFlow skill 开关逻辑/控制面板 UI
  - 改 Docker/nginx 部署配置
- **产品需求应落在 deer-flow/（外部）**
  - 加 LLM 模型、换底层 Agent 框架、加/禁用工具（除了通过本仓库控制面板开关已有 skill）、改记忆/检索后端

## Capabilities
| Capability | Description | Entry | Core modules |
| --- | --- | --- | --- |
| 学生注册（含密码） | 邮箱+姓名+年级+密码注册，PBKDF2 哈希，写库，触发邮件+飞书通知 | `POST /api/register` | [routes.py:70-121](file:///Users/bytedance/Awake/backend/app/api/routes.py#L70-L121), [auth_service.py hash_password](file:///Users/bytedance/Awake/backend/app/services/auth_service.py), [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py), [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) |
| 邮箱+密码登录（JWT） | 验密码哈希，签发 7 天 Bearer token | `POST /api/login` | [routes.py:124-152](file:///Users/bytedance/Awake/backend/app/api/routes.py#L124-L152), [auth_service.py verify_password](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) |
| 当前会话查询 | 校验 JWT，返回当前学生 | `GET /api/auth/me` | [routes.py:155-157](file:///Users/bytedance/Awake/backend/app/api/routes.py#L155-L157), [get_current_student:42-67](file:///Users/bytedance/Awake/backend/app/api/routes.py#L42-L67) |
| 任务创建/查询 | 手动或从对话提炼创建任务 | `POST /api/tasks`, `GET /api/tasks/{id}` | [routes.py:160-202](file:///Users/bytedance/Awake/backend/app/api/routes.py#L160-L202), [routes.py:268-276](file:///Users/bytedance/Awake/backend/app/api/routes.py#L268-L276) |
| 任务打卡 | 幂等完成任务，写反馈，推飞书 | `POST /api/task-complete` | [routes.py:205-254](file:///Users/bytedance/Awake/backend/app/api/routes.py#L205-L254) |
| 学生画像查询 | 返回学生信息+任务列表 | `GET /api/students/{email}` | [routes.py:257-265](file:///Users/bytedance/Awake/backend/app/api/routes.py#L257-L265) |
| 苏格拉底对话 | 透传多轮消息给 DeerFlow/mock，按轮次切换小海阶段 | `POST /api/chat` | [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) |
| 对话提炼任务 | 让 DeerFlow 生成微行动描述并落库 | `POST /api/chat/extract-task` | [routes.py:295-333](file:///Users/bytedance/Awake/backend/app/api/routes.py#L295-L333) |
| DeerFlow 引擎状态 | 代理 gateway `/api/models`（取默认模型）+ 健康探测 | `GET /api/deerflow/status` | [deerflow_control.py get_status](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) |
| DeerFlow Skills 列表 | 代理 gateway `/api/skills`，归一化字段 | `GET /api/deerflow/skills` | [deerflow_control.py list_skills](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) |
| DeerFlow Skill 开关 | 代理 gateway `PUT /api/skills/{name}` | `PUT /api/deerflow/skills/{name}` | [deerflow_control.py set_skill_enabled](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) |
| DeerFlow 模型列表 | 代理 gateway `/api/models`，归一化字段 | `GET /api/deerflow/models` | [deerflow_control.py list_models](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) |
| 健康检查 | 存活探针（Docker HEALTHCHECK 用） | `GET /api/health` | [routes.py:389-391](file:///Users/bytedance/Awake/backend/app/api/routes.py#L389-L391) |

## Interfaces
| Interface | Business meaning | Entry | Compatibility notes |
| --- | --- | --- | --- |
| HTTP REST `/api/*` | 前端 SPA 唯一后端 | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | 契约以 Pydantic schema 为准；除注册、登录、健康检查外均要求 Bearer；学生资源校验归属；DeerFlow 控制接口对学生返回 403 |
| JWT | 登录态 | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | HS256；默认密钥"awaken-dev-secret-change-me"，生产必须通过 `AUTH_SECRET_KEY` 覆盖；有效期 7 天；payload 含 `student_id` + `email` + `exp` |
| PBKDF2 密码哈希 | 注册/登录密码存储 | [auth_service.py hash_password/verify_password](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | 算法 `pbkdf2_sha256`；260k 迭代；16 字节随机盐；格式 `$pbkdf2-sha256$iterations$salt_b64$hash_b64$` |
| SMTP（QQ 邮箱 SSL:465） | 注册欢迎邮件 | [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) | 关闭时 `logger.info` mock，不抛异常；邮件 CTA 用 `FRONTEND_URL/chat?email=...`（旧路径，前端会重定向到 `/app/chat`） |
| 飞书自定义机器人 Webhook | 注册/打卡/任务卡片通知 | [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) | `FEISHU_ENABLED=false` 时仅打日志；任务卡片 `notify_task_created` 当前始终走 logger（未实际 POST webhook） |
| DeerFlow LangGraph 对话 API | 对话推理 | `POST {DEERFLOW_BASE_URL}/api/runs/wait` | 非 OpenAI 兼容；超时 120s；thread_id 用随机 uuid（无状态）；失败自动降级 mock；assistant_id 由 `DEERFLOW_ASSISTANT_ID` 指定 |
| DeerFlow 控制 API | 引擎状态/skills/models 管理 | `GET {DEERFLOW_BASE_URL}/api/models`, `GET/PUT {DEERFLOW_BASE_URL}/api/skills[/{name}]` | 超时由 `DEERFLOW_CONTROL_TIMEOUT_SECONDS`（默认 60s）独立控制；失败返回 online=false 降级态 |

## Interface Inventory
| Capability type | Business meaning | Definition entry | Implementation entry | Test entry | Common change path |
| --- | --- | --- | --- | --- | --- |
| HTTP | 注册（含密码） | [schemas.py:19-23](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L19-L23) | [routes.py:70](file:///Users/bytedance/Awake/backend/app/api/routes.py#L70-L121) | `TestRegisterAPI` | 改字段动 models+schemas+routes；密码策略改 auth_service |
| HTTP | 登录（JWT+密码） | [schemas.py:26-28](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L26-L28) | [routes.py:124](file:///Users/bytedance/Awake/backend/app/api/routes.py#L124-L152) | `TestAuthAPI::test_login_*` | 改密码强度/加验证码→auth_service + schema |
| HTTP | 当前会话（需鉴权） | — | [routes.py:155](file:///Users/bytedance/Awake/backend/app/api/routes.py#L155-L157) | `TestAuthAPI::test_auth_me_*` | 补鉴权时以本接口为参考样板 |
| HTTP | 创建任务 | [schemas.py:43-46](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L43-L46) | [routes.py:160](file:///Users/bytedance/Awake/backend/app/api/routes.py#L160-L202) | `TestTaskAPI` | — |
| HTTP | 任务打卡（幂等） | [schemas.py:49-51](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L49-L51) | [routes.py:205](file:///Users/bytedance/Awake/backend/app/api/routes.py#L205-L254) | `TestTaskCompleteAPI` | 幂等分支必须保留 |
| HTTP | 查询学生 | URL path | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | `TestStudentAPI` | 需鉴权且 email 必须匹配当前学生 |
| HTTP | 对话 | [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) | [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | `TestChatAPI` | 需鉴权；改 prompt 动 config.py |
| HTTP | 对话提炼任务 | [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) | [deerflow_service.py extract_task](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | `TestExtractTaskAPI` | 需鉴权；结构化任务契约 |
| HTTP | DeerFlow 控制接口 | DeerFlow schemas | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | `test_deerflow_control.py` | 普通学生固定 403；内部代理仍保留离线降级 |
| HTTP | 密码哈希 | （工具函数，无路由） | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | `TestPasswordHashing`, `TestPasswordMigration` | 260k 迭代；旧库迁移见 migrations.py |
| Frontend route | 营销落地 | `/` → Landing | [App.jsx:29](file:///Users/bytedance/Awake/frontend/src/App.jsx#L29) | — | 内页禁止复用 marketing 导航 |
| Frontend route | 注册 | `/register` → Register | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | — | 使用 app Navbar |
| Frontend route | 登录 | `/login` → Login | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | — | 使用 app Navbar |
| Frontend route | 注册成功 | `/success` → Success | [App.jsx:32](file:///Users/bytedance/Awake/frontend/src/App.jsx#L32) | — | 使用 `variant="app"`；提供带 `?email=` 的直达按钮 |
| Frontend route | 旧对话路径 | `/chat` → 重定向到 `/app/chat` | [App.jsx:33](file:///Users/bytedance/Awake/frontend/src/App.jsx#L33) | — | LegacyChatRedirect 保留 query string |
| Frontend route | 旧打卡路径 | `/checkin*` → `/app/checkin` | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | — | 保留 query string；demo 转为 `demo=1` |
| Frontend route | Workspace 外壳 | `/app` → WorkspaceLayout | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | — | 透传学生与固定按需连接状态，不请求控制接口 |
| Frontend route | Workspace 学生闭环 | `/app/today`, `/app/chat`, `/app/tasks`, `/app/focus`, `/app/checkin`, `/app/explore`, `/app/growth` | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | — | Sidebar 展示今日/对话/微行动/探索/成长 |
| Frontend route | Workspace 设置 | `/app/settings` → Settings | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | — | 学生资料 + API 健康检查 |
| Frontend route | 旧能力路径 | `/app/capabilities` → `/app/today` | [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | — | 学生端不暴露控制面板 |

## Data And Dependencies
| Resource | Usage | Code location | Failure/compatibility notes |
| --- | --- | --- | --- |
| SQLite | 持久化学生与任务 | [database.py](file:///Users/bytedance/Awake/backend/app/core/database.py), `DATABASE_URL` in [config.py:10](file:///Users/bytedance/Awake/backend/app/core/config.py#L10) | `awaken.db` 在 backend 根目录（已 gitignore）；无 Alembic；init_db 时自动跑 [migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py) 做旧库 ALTER + 密码回填；测试走独立 `test_awaken.db` |
| JWT (jose) | 登录态签发/校验 | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | 密钥从 `AUTH_SECRET_KEY`；默认值仅用于本地开发；payload 含 student_id/email/exp |
| PBKDF2 (hashlib) | 密码哈希 | [auth_service.py hash_password](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | 260k 迭代；16 字节 os.urandom 盐；兼容 passlib 风格格式 `$pbkdf2-sha256$...` |
| DeerFlow（外部，对话） | 对话推理 | `DEERFLOW_BASE_URL` 默认 `http://localhost:8001` | 120s 超时；失败→mock 降级；需配合 DeerFlow 的 `DEER_FLOW_AUTH_DISABLED=1` 本地启动；LangGraph 协议 `/api/runs/wait` |
| DeerFlow（外部，控制） | 引擎管理 | 同上 base_url | 60s 超时（`DEERFLOW_CONTROL_TIMEOUT_SECONDS`）；失败→online=false 降级（不抛 500）；`/api/models`、`/api/skills`、`PUT /api/skills/{name}` |
| QQ SMTP | 欢迎邮件 | [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) | 非必需，`SMTP_ENABLED=false` 走 mock 日志 |
| 飞书 Webhook | 注册/打卡/任务通知 | [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) | Webhook 地址走 `.env`；失败不影响主流程；task_created 当前只打日志 |
| localStorage | 前端 token 与学生信息缓存 | [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) | key: `awaken_access_token` / `awaken_student`；axios 拦截器自动带 Authorization |
| 前端 Vite proxy | 开发态把 `/api` 代理到 `:8000` | [vite.config.js:8-17](file:///Users/bytedance/Awake/frontend/vite.config.js#L8-L17) | `timeout/proxyTimeout` 130s > 后端 httpx 120s |
| 前端 nginx (Docker) | 生产态 SPA + `/api` 反向代理 | [nginx.conf](file:///Users/bytedance/Awake/frontend/nginx.conf) | `proxy_read_timeout 130s`；SPA fallback `try_files $uri /index.html` |

## Configuration
| Config | Purpose | Code location | Risk |
| --- | --- | --- | --- |
| `APP_ENV` / `DEBUG` | 日志级别与 uvicorn reload | [config.py:8-9](file:///Users/bytedance/Awake/backend/app/core/config.py#L8-L9), [main.py](file:///Users/bytedance/Awake/backend/main.py) | 生产必须 `DEBUG=false` |
| `DATABASE_URL` | SQLite 路径 | [config.py:10](file:///Users/bytedance/Awake/backend/app/core/config.py#L10) | 切换到 Postgres 需改 connect_args 与 driver |
| `AUTH_SECRET_KEY` / `AUTH_ALGORITHM` / `AUTH_TOKEN_EXPIRE_MINUTES` | JWT | [config.py:11-13](file:///Users/bytedance/Awake/backend/app/core/config.py#L11-L13) | **生产必须替换默认密钥**；默认值仅限本地 |
| `AUTH_LEGACY_USER_DEFAULT_PASSWORD` | 旧用户密码迁移回填默认值 | [config.py:14](file:///Users/bytedance/Awake/backend/app/core/config.py#L14) | 迁移脚本启动时对 password_hash 为空的行用此值哈希回填；改此值前先确认旧用户数据已迁移完 |
| `SMTP_*` / `SMTP_ENABLED` | 邮件 | [config.py:16-21](file:///Users/bytedance/Awake/backend/app/core/config.py#L16-L21) | 密码是 QQ 邮箱授权码，非登录密码 |
| `FEISHU_*` / `FEISHU_ENABLED` | 飞书通知 | [config.py:23-25](file:///Users/bytedance/Awake/backend/app/core/config.py#L23-L25) | 关闭时日志 mock |
| `DEERFLOW_ENABLED` / `DEERFLOW_BASE_URL` / `DEERFLOW_ASSISTANT_ID` / `DEERFLOW_API_KEY` | DeerFlow 对话连接 | [config.py:27-33](file:///Users/bytedance/Awake/backend/app/core/config.py#L27-L33) | 本地开发需 `DEER_FLOW_AUTH_DISABLED=1` 在 deer-flow 侧；API Key 留空即可 |
| `DEERFLOW_CONTROL_TIMEOUT_SECONDS` | DeerFlow 控制接口超时 | [config.py:35](file:///Users/bytedance/Awake/backend/app/core/config.py#L35) | 默认 60s；与对话 120s 独立，因为 skills/models 响应通常更快 |
| `XIAOHAI_*_PROMPT` / `XIAOHAI_UNLOCK_AFTER_TURNS` | 小海人设与阶段规则 | [config.py:37-58](file:///Users/bytedance/Awake/backend/app/core/config.py#L37-L58) | 阈值必须与 `can_extract_task` 一致（3 轮） |
| `FRONTEND_URL` | 邮件 CTA、飞书卡片跳转 | [config.py:60](file:///Users/bytedance/Awake/backend/app/core/config.py#L60) | 部署后必须改；邮件 CTA 指向 `/chat?email=`，前端会重定向到 `/app/chat` |
| `BACKEND_CORS_ORIGINS` | 允许的前端 Origin | [config.py:61-72](file:///Users/bytedance/Awake/backend/app/core/config.py#L61-L72) | JSON 字符串；部署域名必须加入 |

## Change Ownership
| Requirement type | Preferred landing service/module | Reason |
| --- | --- | --- |
| 改人设/对话阶段/回复语气 | [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) 中 `XIAOHAI_*_PROMPT`，必要时 [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | prompt 是单一事实源 |
| 改接口鉴权 | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) 中复用 `get_current_student` 并校验资源归属 | 前端拦截器已就位；控制面板保持学生 403 |
| 改密码策略/哈希参数 | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) + config.py + migrations.py | 迭代次数/算法改 auth_service；默认迁移密码改 config；新迁移逻辑加 migrations.py |
| 改数据字段 | [models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) + [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) + 对应路由 | ORM/Schema/API 三点齐改；已有数据库需 ALTER（参考 migrations.py 模式） |
| 改 DeerFlow skill 开关/控制面板 | [deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) + [Capabilities.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Capabilities.jsx) | 后端归一化 + 前端 UI；所有异常必须降级为 online=false |
| 改导航/布局 | [WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) / [Sidebar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Sidebar.jsx) / [ContextBar.jsx](file:///Users/bytedance/Awake/frontend/src/components/ContextBar.jsx) / [Navbar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Navbar.jsx) | Workspace 内页用 Sidebar+ContextBar；非 Workspace 页用 Navbar variant 隔离 |
| 改聊天 UI 样式 | [Chat.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Chat.jsx) + global.css | — |
| 加通知渠道 | 新增 service 文件并在对应路由处调用，遵循现有 email/feishu 的 **失败不抛、仅记日志** 约定 | 通知是 best-effort，不能阻塞注册/打卡 |
| 改 Docker/nginx 部署 | [backend/Dockerfile](file:///Users/bytedance/Awake/backend/Dockerfile) / [frontend/Dockerfile](file:///Users/bytedance/Awake/frontend/Dockerfile) / [nginx.conf](file:///Users/bytedance/Awake/frontend/nginx.conf) | 超时链路必须同步改 nginx proxy_read_timeout |
| 换 LLM/加工具/改记忆后端 | 外部 `deer-flow/` 仓库 | 本仓库只调 HTTP API；skill 开关通过本仓库控制面板代理即可 |
