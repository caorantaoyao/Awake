# Agent Rules

未来任何 agent 在本仓库动代码前必须先读本文件。规则以代码现状为唯一依据，非臆想。

## Mandatory（必须遵守）
- 配置与代码分离。所有可变项（URL、端口、密钥、开关、阈值、prompt、密码迭代次数）必须放在 [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) 通过环境变量/`.env` 注入，不得硬编码。
- 对话链路永不抛异常。所有 DeerFlow 对话 HTTP 调用必须有失败兜底（当前为 mock 苏格拉底脚本），调用点禁止把异常裸抛给前端。参考 [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py)。
- DeerFlow 控制接口永不抛 500。`/api/deerflow/*` 接口在 DeerFlow 不可达或代理异常时必须返回 `online: false` 降级响应（带 error 字段），参考 [routes.py:336-386](file:///Users/bytedance/Awake/backend/app/api/routes.py#L336-L386) 的 try/except 模式和 [deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py)。
- 通知（邮件/飞书/新增渠道）是 best-effort：失败只能 `logger.error/return False`，不得让注册/打卡接口 500。
- 前端 Workspace 内页（`/app/*`）**必须**通过 [WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) 外壳渲染（自动包含 Sidebar + ContextBar），不要在页面内手动加 Navbar。
- Landing 使用 marketing Navbar；Register/Login/Success 使用 `<Navbar variant="app" />`。CheckIn 已迁入 Workspace。
- 小海阶段规则（探索期/解锁期）的 system prompt 必须互斥二选一，不能把两段规则同时注入同一 prompt。阈值 `XIAOHAI_UNLOCK_AFTER_TURNS` 必须与 [routes.py:285](file:///Users/bytedance/Awake/backend/app/api/routes.py#L285) 的 `can_extract_task = user_turns >= 3` 保持数值一致。
- 超时链路一致：
  - **对话链路**（chat/extract-task）：前端 axios 130s ≥ Vite proxy 130s ≥ nginx proxy_read_timeout 130s ≥ 后端 httpx 120s。
  - **控制链路**（status/skills/models/toggle）：前端 60s = 后端 `DEERFLOW_CONTROL_TIMEOUT_SECONDS` 60s。
  - 改其中一处必须同时改所有相关处。
- 写接口（注册/任务/打卡/提炼）必须有 `try/except + db.rollback()` 并以合理 HTTP 状态码返回，不得泄漏原始异常到前端。
- 新接口默认应当使用 `Depends(get_current_student)` 做鉴权，除非产品明确要求匿名访问；涉及学生资源时必须按当前 token 身份校验归属。
- 密码哈希必须使用 [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) 提供的 `hash_password/verify_password`，禁止明文存储、禁止自制哈希算法、禁止使用 MD5/SHA1。
- DeerFlow 控制代理返回必须归一化：使用 `_normalize_skills/_normalize_models` 模式把 DeerFlow 原始返回映射到稳定 schema（[schemas.py:101-156](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L101-L156)），用 `ConfigDict(extra="allow")` 透传未知字段。
- 测试环境必须隔离外部服务。[conftest.py:12-15](file:///Users/bytedance/Awake/backend/tests/conftest.py#L12-L15) 通过 `os.environ` 在 import 前强制关闭 SMTP/DeerFlow；为新增的外部服务写测试时遵循同样模式。
- 数据库资源：Session 必须在 `finally` 中关闭（见 [database.py](file:///Users/bytedance/Awake/backend/app/core/database.py)），新增依赖注入点必须沿用 `get_db()`。
- 响应语义统一：成功响应走 `ApiResponse(success=True, message, data)` 约定；单实体查询（`get_student`/`get_task`/`chat`/`health`/`deerflow/*`）可直接返回 Pydantic 模型，保持现状不要混用。
- 前端 Workspace 页面通过 `useOutletContext()` 获取共享状态（`student`, `deerflowStatus`, `currentModel`, `setStudent`, `refreshDeerflowStatus`）；学生工作区不主动请求受限的 DeerFlow 控制接口。

## Forbidden（禁止）
- 禁止在本仓库内修改 `deer-flow/` 下的任何文件或配置（已被 [.gitignore](file:///Users/bytedance/Awake/.gitignore) 排除，独立外部仓库）。
- 禁止把 DeerFlow 对话接口当作 OpenAI 兼容接口调用 `/v1/chat/completions`，必须走 LangGraph 平台协议 `POST /api/runs/wait`。
- 禁止把 SMTP 密码、飞书 Webhook、API Key、JWT 密钥写死在代码或提交到仓库——`.env` 已 gitignore，本地自填。
- 禁止在 routes 里直接写 HTML/长文案作为 response 文本；模板/邮件内嵌 HTML 放到对应 service（如 [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py)）。
- 禁止删除或弱化 `/api/task-complete` 的幂等分支（[routes.py:217-224](file:///Users/bytedance/Awake/backend/app/api/routes.py#L217-L224)），重复打卡必须返回成功并提示"无需重复"。
- 禁止在前端直接访问 `localhost:8001`（DeerFlow），所有对话和控制请求必须经过后端 `/api/*` 编排/代理层。
- 禁止引入状态管理库（Redux/Zustand 等）、UI 组件库（AntD/MUI 等）、CSS-in-JS 库到当前 MVP，保持零额外依赖手写组件。当前 frontend 仅依赖 react + react-router-dom + axios（见 [package.json](file:///Users/bytedance/Awake/frontend/package.json)）。
- 禁止在 CSS 之外硬改像素级样式到 JSX（`style={{...}}`），除非是动态值或一次性、不参与主题的例外（如 `textAlign: 'center'`）。
- 禁止在 migrations.py 中删除已有迁移逻辑；新增迁移必须幂等（重复执行不破坏数据）。
- 禁止把 DeerFlow 控制接口的异常直接抛给前端——所有 `/api/deerflow/*` 必须 catch 后返回降级响应。
- 禁止在前端 Workspace 页面中绕过 Outlet context 手动管理 deerflowStatus/student 的全局状态——用 `setStudent`/`refreshDeerflowStatus` 更新共享状态。

## Compatibility
- **API**：前端通过 axios 直接消费字段名，改字段名/嵌套结构时必须同步改 [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) 与对应页面；新增字段默认允许缺省（`Optional`）。
- **Pydantic v2**：新代码使用 `model_config = ConfigDict(...)`（参考 DeerFlow* schemas）；旧 schema 仍用 `class Config: from_attributes = True`。新增 schema 推荐用 ConfigDict 风格，不要混用造成风格断裂。
- **SQLAlchemy 2.0**：使用 `query()` 风格（现状），新增代码保持风格一致；不要混用 select() 风格造成文件内风格断裂。
- **Enum**：`GradeEnum` / `TaskStatusEnum` 是 `str, enum.Enum`，存储的是中文值（"高一"/"进行中" 等），前端直接展示用。不要改成 int 枚举——会破坏已有数据。
- **DB 文件**：`awaken.db` 在 backend 根目录，已 gitignore；切换 Postgres/MySQL 时必须同时改 [database.py](file:///Users/bytedance/Awake/backend/app/core/database.py) 的 `connect_args`（SQLite 专属 `check_same_thread=False`）。
- **DeerFlow thread_id**：当前每次对话请求都用新的 `uuid.uuid4()`，即**无状态对话**（所有历史由前端 `messages` 数组全量携带）。不要改成长连接 thread 复用，除非同时引入会话存储与历史裁剪。
- **前端路由**：`/chat?email=...` 是邮件 CTA 和 Success 页直达按钮的旧目标格式，前端会重定向到 `/app/chat?email=...`。改路径或参数名必须同步改 [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) 和 [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py)。
- **Config JSON 字段**：`BACKEND_CORS_ORIGINS` 是 JSON 字符串，解析失败兜底默认值，见 [config.py:67-72](file:///Users/bytedance/Awake/backend/app/core/config.py#L67-L72)；改格式需同步改解析逻辑。
- **密码哈希格式**：`hash_password` 输出 `$pbkdf2-sha256$iterations$salt_b64$hash_b64$` 格式（兼容 passlib 风格）。`verify_password` 能处理无效 hash 格式（返回 False 而非抛异常）。
- **旧用户迁移幂等性**：[migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py) 的 `migrate_password_hashes` 只对 `password_hash IS NULL` 的行回填，重复执行不会覆盖已有 hash。改 `AUTH_LEGACY_USER_DEFAULT_PASSWORD` 前确认旧用户已完成迁移。
- **DeerFlow 控制超时独立**：对话超时（120s/130s）和控制超时（60s）是两套独立配置，不要把控制接口超时也设成 120s——控制接口通常秒级返回，60s 已足够。
- **Workspace Outlet context**：[WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) 通过 `<Outlet context={...} />` 透传 5 个值，新增页面需要消费时用 `useOutletContext()` 解构，不要通过 props drilling 传递。

## Security
- **JWT 默认密钥必须在生产覆盖**：[config.py:11](file:///Users/bytedance/Awake/backend/app/core/config.py#L11) 默认 `AUTH_SECRET_KEY="awaken-dev-secret-change-me"` 仅用于本地；部署必须通过环境变量设置高强度随机密钥，否则任何人都能伪造 token。
- **业务接口信任边界**：学生业务接口已挂 `Depends(get_current_student)` 并校验资源归属；请求体、URL 参数和旧链接中的 email 都不能代替 token 身份。新增接口必须保持这一边界。
- **密码存储**：使用 PBKDF2_SHA256 + 260k 迭代 + 16 字节随机盐，符合当前 OWASP 最低推荐。不要降级迭代次数；未来升级到 Argon2id 需要做透明迁移（verify 时识别旧格式并 rehash）。
- **旧用户默认密码风险**：`AUTH_LEGACY_USER_DEFAULT_PASSWORD` 用于迁移回填，所有迁移前已存在的用户共享此密码。生产环境必须在迁移后立即通知用户重置密码，或在首次登录时强制改密。
- **敏感数据**：禁止日志打印 AUTH_SECRET_KEY、SMTP 密码、飞书 Webhook URL 全量、完整 JWT、学生完整 email（如需日志只打印前缀+脱敏）、密码明文、密码 hash 全量。
- **CORS**：生产必须通过 `BACKEND_CORS_ORIGINS` 限定为实际域名；禁止部署时保留 `allow_origins=["*"]`。
- **输入校验**：所有写接口必须走 Pydantic（`Field(...)`、`EmailStr`、`min_length`），不要在路由内手写 `if not x: raise 400`。密码字段 `min_length=8, max_length=128`。
- **飞书 URL**：卡片里的 `FRONTEND_URL` 会被拼进按钮 href，确保不注入 `javascript:` 等危险 scheme（FastAPI 会对 str 返回做转义，但配置项本身需人工把关）。
- **HTML 邮件**：内嵌 HTML 目前使用 f-string 拼接姓名（[email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py)），用户输入的 `student_name` 会直接进入 HTML；如允许用户自定义昵称含 `<`/`>` 需做 HTML 转义。MVP 阶段姓名长度上限 100，风险可控。
- **localStorage 明文存储**：前端把 access_token 和 student 对象明文存 `localStorage`（[client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js)），存在 XSS 泄露风险；引入第三方脚本前必须评估。
- **DeerFlow 控制接口对学生封闭**：`/api/deerflow/*` 先校验 token，再通过 `deny_student_control_access` 对普通学生返回 403。不得为了复用内部联调 UI 放宽此限制。

## Known Pitfalls（已知陷阱）
- **SQLite 无自动迁移**：改 Column 后旧 `awaken.db` 会报错。已有迁移基础设施：在 [migrations.py](file:///Users/bytedance/Awake/backend/app/core/migrations.py) 加幂等 ALTER（参考 `migrate_password_hashes` 模式），init_db 会自动执行；本地快速迭代可删 `backend/awaken.db` 重建。生产部署**必须**确保迁移逻辑完备再上线。
- **DeerFlow mock 降级会被误判为"接口坏了"**：当 `DEERFLOW_ENABLED=true` 但 DeerFlow 没启动时，对话接口 200 但 `mode=mock`，前端不会报错。排查对话质量问题时先看后端日志里有没有 "DeerFlow chat 调用失败，降级到 mock"。
- **DeerFlow 控制接口降级是 200 不是 500**：DeerFlow 离线时，`/api/deerflow/*` 返回 HTTP 200 + `online: false`，不要在前端用 `response.ok` 判断 DeerFlow 是否可用——必须检查 `online` 字段。
- **DeerFlow 非 OpenAI**：不要尝试把 `base_url` 塞给 openai SDK，会 404。
- **CORS_ORIGINS 是 JSON 字符串**：`.env` 里写 `BACKEND_CORS_ORIGINS=["http://a","http://b"]`，**不要**用逗号分隔字符串，否则会走到 fallback 默认值。
- **前端 API baseURL 是 `/api`**：[client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) 相对路径依赖 Vite 代理/nginx 反代；生产部署必须在反向代理层把 `/api` 转发到后端 8000，或改成绝对 URL。
- **聊天消息的空白换行**：AI 回复有多段文本时，气泡必须支持 `white-space: pre-wrap`（当前已在 CSS 设置，重构样式时不要丢）。
- **测试 DB 清理**：[conftest.py:35](file:///Users/bytedance/Awake/backend/tests/conftest.py#L35) 每个用例后 `drop_all`，如果新增测试里手动建连接/会话，记得关闭否则 SQLite 文件锁可能导致下一个用例失败。
- **Feishu task_created 当前始终走 mock 日志**：[feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) 没有调用 `_send_webhook`（目前只生成卡片 payload 并打日志）。真要推飞书需补 webhook URL 字段 + `_send_webhook` 调用。
- **Task.feedback 字段已确认使用**：CheckIn 页会把 textarea 内容（空串转 null）传给 `/api/task-complete`。
- **旧邮件链接只兼容导航**：`/chat?email=...` 会保留 query string 重定向到 Workspace，但没有 token 时仍需登录；不得恢复“凭 email 访问”的旧行为。
- **Pydantic schema 风格不一致**：StudentResponse/TaskResponse 等旧 schema 用 `class Config: from_attributes = True`，DeerFlow* 新 schema 用 `model_config = ConfigDict(extra="allow")`。重构旧 schema 时可以统一迁移到 ConfigDict 风格，但不要在不相关改动中夹带。
- **Workspace 不读取控制面板快照**：[WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) 为学生端提供固定的按需连接状态；不要在挂载时请求学生无权访问的 status/models 接口。
- **前端 client.js 的 control 超时环境变量**：`VITE_DEERFLOW_CONTROL_TIMEOUT_MS` 可覆盖默认 60s 控制接口超时，但后端的 `DEERFLOW_CONTROL_TIMEOUT_SECONDS` 不会读前端环境变量——两边独立配置，改时记得同步。
