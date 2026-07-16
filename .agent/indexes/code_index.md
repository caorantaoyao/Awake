# Code Index

面向未来 agent 的代码地图：遇到关键词先查这里，再打开文件。

## Entry Points
| Area | Path | Notes |
| --- | --- | --- |
| Backend bootstrap | [backend/main.py](file:///Users/bytedance/Awake/backend/main.py) | FastAPI app 实例、CORS、startup hook（init_db + 迁移）、uvicorn 入口 |
| HTTP routes | [backend/app/api/routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | 所有 `/api/*` 端点一文件集中管理（含 DeerFlow 控制 4 接口） |
| Config / env / prompts | [backend/app/core/config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) | Settings 单例；JWT 密钥/有效期、密码哈希参数、小海人设/阶段 prompt/阈值、DeerFlow 连接/控制超时全部在这里 |
| JWT + 密码哈希工具 | [backend/app/services/auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | `create_access_token` / `decode_access_token` / `hash_password` / `verify_password`；PBKDF2_SHA256，260k 迭代 |
| 鉴权依赖 | [backend/app/api/routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | `get_current_student` + HTTPBearer；学生业务接口校验身份与资源归属；控制接口通过 `deny_student_control_access` 返回 403 |
| DB engine & session | [backend/app/core/database.py](file:///Users/bytedance/Awake/backend/app/core/database.py) | `Base`, `get_db()`, `init_db()`；SQLite 专用 `check_same_thread=False`；init_db 自动调用迁移 |
| SQLite 迁移 | [backend/app/core/migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py) | `migrate_password_hashes()`：ALTER TABLE 加 password_hash 列 + 旧行用默认密码回填；幂等 |
| 迁移脚本入口 | [backend/scripts/migrate_password_hashes.py](file:///Users/bytedance/Awake/backend/scripts/migrate_password_hashes.py) | 独立脚本，手动触发密码迁移 |
| ORM models | [backend/app/models/models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) | `Student`(含 password_hash), `Task`, `GradeEnum`, `TaskStatusEnum` |
| Pydantic schemas | [backend/app/schemas/schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) | 请求/响应契约；DeerFlow* 系列 schema 使用 `ConfigDict(extra="allow")`；其余用旧 `class Config` |
| DeerFlow 对话适配 | [backend/app/services/deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | LangGraph 协议适配、system prompt 组装（两阶段互斥）、mock 降级、回复解析 |
| DeerFlow 控制面板代理 | [backend/app/services/deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) | `get_status` / `list_skills` / `set_skill_enabled` / `list_models`；归一化 `_normalize_skills/_normalize_models`；httpx 调用；异常→online=false 降级 |
| Email service | [backend/app/services/email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) | SMTP 发送 + HTML 邮件模板，关闭时 mock |
| Feishu webhook | [backend/app/services/feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) | 注册/打卡/任务卡片 webhook，best-effort；task_created 仅打日志 |
| Backend Dockerfile | [backend/Dockerfile](file:///Users/bytedance/Awake/backend/Dockerfile) | python:3.11-slim，端口 8000，HEALTHCHECK 调 `/api/health` |
| Tests | [backend/tests/](file:///Users/bytedance/Awake/backend/tests) | pytest；[conftest.py](file:///Users/bytedance/Awake/backend/tests/conftest.py) 强制隔离外部服务（SMTP/DeerFlow mock）；[test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) 覆盖所有端点；[test_deerflow_control.py](file:///Users/bytedance/Awake/backend/tests/test_deerflow_control.py) 覆盖控制面板降级逻辑 |
| Frontend bootstrap | [frontend/src/main.jsx](file:///Users/bytedance/Awake/frontend/src/main.jsx) → [index.html](file:///Users/bytedance/Awake/frontend/index.html) | React 挂载点 |
| Frontend 路由表 | [frontend/src/App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | SPA 路由；`/app` 子路由用 WorkspaceLayout；`/chat` 重定向到 `/app/chat`；顶层保留 `/ /register /login /success /checkin /checkin/demo` |
| Workspace 外壳 | [frontend/src/layouts/WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) | Sidebar + ContextBar + Outlet；不请求学生受限的控制接口；通过 Outlet context 透传共享状态 |
| API client | [frontend/src/api/client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) | axios 实例；token localStorage 存取；请求拦截器自动带 Authorization；chat/extract-task 超时 130s；DeerFlow 控制接口 60s（可被 `VITE_DEERFLOW_CONTROL_TIMEOUT_MS` 覆盖） |
| Sidebar | [frontend/src/components/Sidebar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Sidebar.jsx) | 学生导航：今日、对话、微行动、探索、成长；设置独立置底；支持折叠/移动端抽屉 |
| ContextBar | [frontend/src/components/ContextBar.jsx](file:///Users/bytedance/Awake/frontend/src/components/ContextBar.jsx) | 当前区域标题、学生信息与面向学生的小海可用状态 |
| Navbar | [frontend/src/components/Navbar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Navbar.jsx) | `variant="marketing"|"app"` 双模式；Landing 用 marketing，Register/Login/Success 用 app |
| Toast | [frontend/src/components/Toast.jsx](file:///Users/bytedance/Awake/frontend/src/components/Toast.jsx) | 全局通知组件 |
| Pages | [frontend/src/pages/](file:///Users/bytedance/Awake/frontend/src/pages) | 学生闭环页面含 Today / Chat / Tasks / Focus / CheckIn / Explore / Growth / Settings；Capabilities 仅保留内部联调代码 |
| Styles | [frontend/src/styles/global.css](file:///Users/bytedance/Awake/frontend/src/styles/global.css) | 全局样式单文件（含 Workspace/tasks/capabilities/settings 样式） |
| Vite config | [frontend/vite.config.js](file:///Users/bytedance/Awake/frontend/vite.config.js) | dev port=3000；`/api` → `:8000` proxy；超时 130s |
| Frontend Dockerfile | [frontend/Dockerfile](file:///Users/bytedance/Awake/frontend/Dockerfile) | 多阶段构建 node:20-alpine → nginx:1.27-alpine |
| Nginx config (Docker) | [frontend/nginx.conf](file:///Users/bytedance/Awake/frontend/nginx.conf) | SPA fallback (`try_files $uri /index.html`) + `/api/` 反向代理到 backend:8000；proxy_read_timeout 130s |
| Env example | [backend/.env.example](file:///Users/bytedance/Awake/backend/.env.example) | 所有后端配置项模板，含新增的密码/DeerFlow 控制相关项 |

## Keyword Routing
| Product/code keyword | Start here | Then check | Notes |
| --- | --- | --- | --- |
| 注册、register、signup、密码、password | [routes.py:70](file:///Users/bytedance/Awake/backend/app/api/routes.py#L70-L121) | [pages/Register.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Register.jsx), auth_service.hash_password, email_service | 密码 min_length=8；重复邮箱返回 400；Register.jsx 有确认密码前端校验 |
| 登录、login、JWT、token、鉴权、auth | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py), [pages/Login.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Login.jsx), [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) | 登录验密码哈希；学生业务接口校验 token 与资源归属 |
| get_current_student、Bearer、Authorization | [routes.py:42-67](file:///Users/bytedance/Awake/backend/app/api/routes.py#L42-L67) | HTTPBearer 依赖；加鉴权时参考 `/api/auth/me` | — |
| 密码哈希、PBKDF2、hash_password、verify_password | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | config.py（无迭代次数配置，硬编码 260k）| 格式 `$pbkdf2-sha256$iterations$salt$hash` |
| 旧用户迁移、migrate、legacy password | [migrations.py](file:///Users/Users/bytedance/Awake/backend/app/core/migrations.py) | database.py init_db 调用；config.py AUTH_LEGACY_USER_DEFAULT_PASSWORD | 幂等：已有 hash 的行不会被覆盖；独立脚本在 scripts/ |
| 任务、task、微行动、任务管理 | [models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) | routes.py `/api/tasks*`, Today.jsx, Tasks.jsx, Focus.jsx, CheckIn.jsx | 今日任务选择、专注计时、打卡与历史列表 |
| 打卡、check-in、complete | [routes.py:205](file:///Users/bytedance/Awake/backend/app/api/routes.py#L205-L254) | CheckIn.jsx, feishu_service `notify_task_complete` | 幂等：已完成直接返回 |
| 对话、chat、小海、Socratic | [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | [Chat.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Chat.jsx), config.py `XIAOHAI_*` | 非 OpenAI 协议；mock 兜底；两阶段 prompt 互斥 |
| DeerFlow、LangGraph、assistant、gateway | [deerflow_service.py:42-66](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) (对话) + [deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) (控制) | config.py `DEERFLOW_*` | 对话 `/api/runs/wait`；控制 `/api/models`、`/api/skills` |
| skill 开关、能力控制、capabilities、web_search 开关 | [deerflow_control.py set_skill_enabled](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) | [Capabilities.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Capabilities.jsx) (SkillToggle 按钮), routes.py `/api/deerflow/skills/{name}` | 后端代理→DeerFlow；离线时按钮 disabled |
| 模型列表、model | [deerflow_control.py list_models](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) | [Capabilities.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Capabilities.jsx) 内部联调代码 | 学生路由不暴露控制面板 |
| 引擎状态、在线/离线 | [deerflow_control.py get_status](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) | Workspace 使用固定按需连接状态；Capabilities 供内部联调 | 学生请求 `/api/deerflow/*` 返回 403 |
| 联网搜索、工具调用、web_search | 外部 `deer-flow/` 仓库 | config.yaml（deer-flow 侧，已 gitignore） | 本仓库可通过 Capabilities 页开关已加载的 skill |
| prompt、人设、苏格拉底、探索期/解锁期 | [config.py:37-58](file:///Users/bytedance/Awake/backend/app/core/config.py#L37-L58) | [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py)（prompt 组装） | 两段 prompt 互斥二选一，阈值=3 |
| can_extract_task、提炼任务、微行动生成 | [routes.py:284-285](file:///Users/bytedance/Awake/backend/app/api/routes.py#L284-L285), [Chat.jsx:242-258](file:///Users/bytedance/Awake/frontend/src/pages/Chat.jsx#L242-L258) | `/api/chat/extract-task` | user 轮次≥3 时出现 |
| 超时、timeout | [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) (chat 130s/control 60s), [vite.config.js:13-14](file:///Users/bytedance/Awake/frontend/vite.config.js#L13-L14) (130s), [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) (120s), [deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) (60s), [nginx.conf](file:///Users/bytedance/Awake/frontend/nginx.conf) (130s) | 五处必须保持：chat 链路前端 130s ≥ Vite/nginx 130s ≥ 后端 httpx 120s；control 接口 60s 独立 |
| Workspace、侧边栏、Sidebar、ContextBar | [WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) | [Sidebar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Sidebar.jsx), [ContextBar.jsx](file:///Users/bytedance/Awake/frontend/src/components/ContextBar.jsx) | Outlet context 透传 deerflowStatus/student；所有 /app/* 页面共享 |
| CORS、跨域 | [main.py](file:///Users/bytedance/Awake/backend/main.py), [config.py:61-72](file:///Users/bytedance/Awake/backend/app/core/config.py#L61-L72) | vite proxy（开发）/nginx proxy（Docker） | 部署要更新 `BACKEND_CORS_ORIGINS` |
| 邮件、SMTP、欢迎邮件、CTA | [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) | config.py `SMTP_*`, `FRONTEND_URL` | HTML 模板内嵌；关闭时仅记日志；CTA 链接指向 `/chat?email=` |
| 飞书、webhook、卡片 | [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) | config.py `FEISHU_*` | best-effort，失败不抛；task_created 只打日志 |
| 导航、Navbar、登录/注册按钮 | [Navbar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Navbar.jsx) | App.jsx 各页面 | Landing 用 marketing；Register/Login/Success 用 app；Workspace 不用 Navbar |
| 数据库、SQLite、awaken.db、迁移 | [database.py](file:///Users/bytedance/Awake/backend/app/core/database.py), [migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py) | models.py, DATABASE_URL | 已有迁移机制（ALTER+回填），但无 Alembic；新增字段参考 migrations.py 模式 |
| Docker、部署、nginx、容器 | [backend/Dockerfile](file:///Users/bytedance/Awake/backend/Dockerfile), [frontend/Dockerfile](file:///Users/bytedance/Awake/frontend/Dockerfile), [nginx.conf](file:///Users/bytedance/Awake/frontend/nginx.conf) | — | backend HEALTHCHECK 调 /api/health；nginx proxy_read_timeout 130s |
| 测试、pytest、TestClient、mock | [conftest.py](file:///Users/bytedance/Awake/backend/tests/conftest.py), [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py), [test_deerflow_control.py](file:///Users/bytedance/Awake/backend/tests/test_deerflow_control.py) | 独立 test_awaken.db；强制 SMTP/DeerFlow mock（DEERFLOW_ENABLED=false, SMTP_ENABLED=false）| 跑前确保 backend 根目录可写 |

## Common Investigation Paths
### 加或改一个返回字段
1. 改 [models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) Column
2. 若数据库已有数据：在 [migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py) 加 ALTER 逻辑（参考 `migrate_password_hashes` 模式），或本地删 `awaken.db` 重建
3. 改 [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) 对应 Response 字段
4. 若需要输入，改 Request schema
5. 检查路由是否需要赋值/返回该字段
6. 前端 [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) + 页面消费处
7. 跑 `pytest`；前端 `npm run build`

### 加或改对话/domain 逻辑
1. prompt 层：优先改 [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) 的 `XIAOHAI_*_PROMPT` 或阈值
2. 编排层（组装 messages、解析回复、mock）：改 [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py)
3. 触发条件/路由：改 [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) `/api/chat*`
4. 阈值一致性：`XIAOHAI_UNLOCK_AFTER_TURNS` == `can_extract_task` 判断中的 `>= 3`
5. 跑 `pytest tests/test_api.py::TestChatAPI tests/test_api.py::TestExtractTaskAPI`；本地走一次三用户轮对话验证

### 加或改 DeerFlow 控制面板功能
1. 后端代理：在 [deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) 加方法，遵循"httpx 调用→归一化→异常捕获→返回 online=false 降级"模式
2. Schema：在 [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) 加 DeerFlow* 响应模型，使用 `model_config = ConfigDict(extra="allow")`
3. 路由：在 [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) `/api/deerflow/*` 段加端点，外层包 try/except 返回降级
4. 前端 client：[client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) 加方法，超时用 controlTimeoutMs（60s）
5. 前端页面：在 [Capabilities.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Capabilities.jsx) 或新页面加 UI，离线时降级只读
6. WorkspaceLayout 若需启动时拉取新快照：在 [WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) 的 loadDeerflowSnapshot 加调用
7. 在 [test_deerflow_control.py](file:///Users/bytedance/Awake/backend/tests/test_deerflow_control.py) 加离线降级测试
8. 跑 `pytest tests/test_deerflow_control.py`；前端 `npm run build`

### 加或改一个外部通知
1. 参考 [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) / [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) 建 service 类，单例 `xxx_service = XxxService()`
2. Config 加 `XXX_ENABLED` + 开关字段，默认 `False`
3. 失败只 `logger.error` 并返回 False，**不要向上抛**
4. 在对应路由 `try/except` 块内调用
5. [conftest.py](file:///Users/bytedance/Awake/backend/tests/conftest.py) 里把该外部服务设为禁用，避免测试打外网

### 加一个 HTTP 接口
1. 在 [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) 加 Request/Response
2. 在 [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) 加 `@router`，写 `db` 依赖与错误码；写接口默认加 `Depends(get_current_student)`
3. 若调用 DeerFlow/外部服务：确保有 mock/降级（对话走 deerflow_service，控制走 deerflow_control 的 online=false 模式）
4. 前端 [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) 加方法；页面按需调用
5. 在 [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) 加 200/4xx 用例
6. 跑 `pytest`

### 加一个 Workspace 内页（/app/*）
1. 新建 `frontend/src/pages/Xxx.jsx`，通过 `useOutletContext()` 获取 `{student, deerflowStatus, currentModel, setStudent, refreshDeerflowStatus}`
2. [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) 在 `/app` 下加 `<Route path="xxx" element={<Xxx />} />`
3. [Sidebar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Sidebar.jsx) 加导航项
4. [ContextBar.jsx](file:///Users/bytedance/Awake/frontend/src/components/ContextBar.jsx) 在 SECTION_TITLES 加路由到标题的映射
5. 无需手动包 Navbar/侧边栏——WorkspaceLayout 外壳已包含
6. API 调用复用 [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js)
7. `npm run build` 验证

### 加一个非 Workspace 页面（顶层路由）
1. 新建 `frontend/src/pages/Xxx.jsx`，手动加 `<Navbar variant="app" />`（营销页用默认 marketing）
2. [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) 顶层加 `<Route path="/xxx" element={<Xxx />} />`
3. `npm run build` 验证

### 排查超时/长回复失败
1. 后端 httpx 对话超时：[deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py)（120s）
2. 后端 httpx 控制超时：[deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py)（60s，由 `DEERFLOW_CONTROL_TIMEOUT_SECONDS` 配置）
3. Vite 代理超时：[vite.config.js:13-14](file:///Users/bytedance/Awake/frontend/vite.config.js#L13-L14)（130s）
4. 前端 axios 对话超时：[client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js)（chat 130s，control 60s）
5. Nginx 超时（Docker）：[nginx.conf](file:///Users/bytedance/Awake/frontend/nginx.conf)（proxy_read_timeout 130s）
6. 必须满足：chat 链路前端 130s ≥ Vite/nginx 130s ≥ httpx 120s；control 链路独立 60s，不要只改一处

### 给业务接口补鉴权
1. 模板参考 [routes.py:155-157](file:///Users/bytedance/Awake/backend/app/api/routes.py#L155-L157)，给接口加 `current_student: Student = Depends(get_current_student)`
2. 把请求体里的 `student_email` 改为从 `current_student.email` 取，避免前端伪造
3. 前端拦截器 [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) 已自动带 token，无需改前端请求
4. **兼容性决策**（先选再动）：
   - 保持 `/app/chat?email=...` 邮件链接可用 → 需在 Chat 页首次进入时用 email 调 `/api/login` 换 token 再继续（但登录需要密码，此路不通；需引入 Magic Link 一次性 token）
   - 或废弃邮件链接统一要求登录 → 同步改 [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) CTA、飞书卡片
   - 或给邮件链接加签名 token（如 JWT 限单次/限时）
5. 注意 DeerFlow 控制面板（`/api/deerflow/*`）是否也需要鉴权——这些接口不涉及学生数据，但可被滥用来开关 skill
6. 补 [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) 未带 token 返回 401 的用例
7. 跑 `pytest`；手动走"邮件链接直达"和"登录后进入"两条路径验证

### 排查 DeerFlow 控制接口异常
1. 确认 DeerFlow 是否在 `:8001` 运行
2. 后端日志搜索 "DeerFlow status/skills/models 代理异常"
3. 前端 Capabilities/Settings 页会显示 offline warning banner，ContextBar 引擎 dot 变红色
4. 所有控制接口都有兜底：即使 DeerFlow 完全挂掉也返回 200 + `online: false`，不会 500
5. 测试覆盖离线降级：`pytest tests/test_deerflow_control.py`
