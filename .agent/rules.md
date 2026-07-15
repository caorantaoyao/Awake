# Agent Rules

未来任何 agent 在本仓库动代码前必须先读本文件。规则以代码现状为唯一依据，非臆想。

## Mandatory（必须遵守）
- 配置与代码分离。所有可变项（URL、端口、密钥、开关、阈值、prompt）必须放在 [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) 通过环境变量/`.env` 注入，不得硬编码。
- 对话链路永不抛异常。所有 DeerFlow/外部 HTTP 调用必须有失败兜底（当前为 mock 苏格拉底脚本），调用点禁止把异常裸抛给前端。参考 [deerflow_service.py:110-123](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L110-L123)。
- 通知（邮件/飞书/新增渠道）是 best-effort：失败只能 `logger.error/return False`，不得让注册/打卡接口 500。
- 前端内页（Chat、CheckIn、Success 以及未来新增的功能页）一律使用 `<Navbar variant="app" />`，不得复用地表页的营销导航与"立即注册/登录"。见 [Navbar.jsx:6-7](file:///Users/bytedance/Awake/frontend/src/components/Navbar.jsx#L6-L7)。
- 小海阶段规则（探索期/解锁期）的 system prompt 必须互斥二选一，不能把两段规则同时注入同一 prompt。阈值 `XIAOHAI_UNLOCK_AFTER_TURNS` 必须与 [routes.py:272](file:///Users/bytedance/Awake/backend/app/api/routes.py#L272) 的 `can_extract_task = user_turns >= 3` 保持数值一致。
- 超时链路一致：前端 axios 超时 ≥ Vite proxy 超时 ≥ 后端 httpx 超时（当前 130s / 130s / 120s）。改其中一处必须同时改另外两处。
- 写接口（注册/任务/打卡/提炼）必须有 `try/except + db.rollback()` 并以合理 HTTP 状态码返回，不得泄漏原始异常到前端。
- 新接口默认应当使用 `Depends(get_current_student)` 做鉴权（参考 [routes.py:142-144](file:///Users/bytedance/Awake/backend/app/api/routes.py#L142-L144)），除非产品明确要求匿名访问；现有未鉴权的业务接口属技术债，不应作为新增接口的模仿样板。
- 测试环境必须隔离外部服务。[conftest.py:12-13](file:///Users/bytedance/Awake/backend/tests/conftest.py#L12-L13) 通过 `os.environ` 在 import 前强制关闭 SMTP/DeerFlow；为新增的外部服务写测试时遵循同样模式。
- 数据库资源：Session 必须在 `finally` 中关闭（见 [database.py:16-21](file:///Users/bytedance/Awake/backend/app/core/database.py#L16-L21)），新增依赖注入点必须沿用 `get_db()`。
- 响应语义统一：成功响应走 `ApiResponse(success=True, message, data)` 约定；单实体查询（`get_student`/`get_task`/`chat`/`health`）可直接返回 Pydantic 模型，保持现状不要混用。

## Forbidden（禁止）
- 禁止在本仓库内修改 `deer-flow/` 下的任何文件或配置（已被 [.gitignore](file:///Users/bytedance/Awake/.gitignore) 排除，独立外部仓库）。
- 禁止把 DeerFlow 当作 OpenAI 兼容接口调用 `/v1/chat/completions`，必须走 LangGraph 平台协议 `POST /api/runs/wait`。
- 禁止把 SMTP 密码、飞书 Webhook、API Key 写死在代码或提交到仓库——`.env` 已 gitignore，本地自填。
- 禁止在 routes 里直接写 HTML/长文案作为 response 文本；模板/邮件内嵌 HTML 放到对应 service（如 [email_service.py:24-62](file:///Users/bytedance/Awake/backend/app/services/email_service.py#L24-L62)）。
- 禁止删除或弱化 `/api/task-complete` 的幂等分支（[routes.py:141-148](file:///Users/bytedance/Awake/backend/app/api/routes.py#L141-L148)），重复打卡必须返回成功并提示"无需重复"。
- 禁止在前端直接访问 `localhost:8001`（DeerFlow），所有对话必须经过后端 `/api/chat` 编排层。
- 禁止引入状态管理库（Redux/Zustand 等）、UI 组件库（AntD/MUI 等）到当前 MVP，保持零依赖手写组件。当前仅依赖 react + react-router-dom + axios（见 [package.json](file:///Users/bytedance/Awake/frontend/package.json)）。
- 禁止在 CSS 之外硬改像素级样式到 JSX（`style={{...}}`），除非是动态值（如 `textAlign: 'center'` 这种一次性、不参与主题的例外）。
- 禁止为 SQLite 引入 Alembic 迁移（当前 MVP 无迁移框架；加字段以删库重建为本地开发约定；若要上生产需先引入迁移，见 Pitfalls）。

## Compatibility
- **API**：前端通过 axios 直接消费字段名，改字段名/嵌套结构时必须同步改 [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) 与对应页面；新增字段默认允许缺省（`Optional`）。
- **Pydantic v2**：使用 `model_validate`（不是 `from_orm`），`class Config: from_attributes = True`（见 [schemas.py:33-34](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py#L33-L34)）。
- **SQLAlchemy 2.0**：使用 `query()` 风格（现状），新增代码保持风格一致；不要混用 select() 风格造成文件内风格断裂。
- **Enum**：`GradeEnum` / `TaskStatusEnum` 是 `str, enum.Enum`，存储的是中文值（"高一"/"进行中" 等），前端直接展示用。不要改成 int 枚举——会破坏已有数据。
- **DB 文件**：`awaken.db` 在 backend 根目录，已 gitignore；切换 Postgres/MySQL 时必须同时改 [database.py](file:///Users/bytedance/Awake/backend/app/core/database.py) 的 `connect_args`（SQLite 专属 `check_same_thread=False`）。
- **DeerFlow thread_id**：当前每次请求都用新的 `uuid.uuid4()`，即**无状态对话**（所有历史由前端 `messages` 数组全量携带）。不要改成长连接 thread 复用，除非同时引入会话存储与历史裁剪。
- **前端路由**：`/chat?email=...` 是邮件 CTA 和 Success 页直达按钮的目标格式（[email_service.py:22](file:///Users/bytedance/Awake/backend/app/services/email_service.py#L22)、[feishu_service.py:90](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py#L90)）。改路径或参数名必须同步改这两处。
- **Config JSON 字段**：`BACKEND_CORS_ORIGINS` 是 JSON 字符串，解析失败兜底默认值，见 [config.py:61-66](file:///Users/bytedance/Awake/backend/app/core/config.py#L61-L66)；改格式需同步改解析逻辑。

## Security
- **JWT 默认密钥必须在生产覆盖**：[config.py:11](file:///Users/bytedance/Awake/backend/app/core/config.py#L11) 默认 `AUTH_SECRET_KEY="awaken-dev-secret-change-me"` 仅用于本地；部署必须通过环境变量设置高强度随机密钥，否则任何人都能伪造 token。
- **业务接口鉴权未完成（关键风险）**：JWT 工具、`POST /api/login`、`GET /api/auth/me`、前端拦截器已就位，但 `/api/chat`、`/api/chat/extract-task`、`/api/tasks`、`/api/task-complete`、`/api/students/{email}`、`/api/tasks/{id}` 仍未挂 `Depends(get_current_student)`，攻击者仅凭已知邮箱即可冒充读写他人数据与对话。**在全量补完鉴权之前，禁止在 Student/Task 上加入任何敏感字段**（身份证、真实成绩、联系方式、家庭信息等）。
- **登录无密码**：`POST /api/login` 当前仅校验邮箱存在即签发 token（[routes.py:121-128](file:///Users/bytedance/Awake/backend/app/api/routes.py#L121-L128)），这是 MVP 阶段的"邮箱认领"机制，等同于 Magic Link 但缺一次性 token；在加密码/验证码前不要作为强身份承诺。
- **敏感数据**：禁止日志打印 AUTH_SECRET_KEY、SMTP 密码、飞书 Webhook URL 全量、完整 JWT、学生完整 email（如需日志只打印前缀+脱敏）。
- **CORS**：生产必须通过 `BACKEND_CORS_ORIGINS` 限定为实际域名；禁止部署时保留 `allow_origins=["*"]`。
- **输入校验**：所有写接口必须走 Pydantic（`Field(...)`、`EmailStr`、`min_length`），不要在路由内手写 `if not x: raise 400`。
- **飞书 URL**：卡片里的 `FRONTEND_URL` 会被拼进按钮 href，确保不注入 `javascript:` 等危险 scheme（FastAPI 会对 str 返回做转义，但配置项本身需人工把关）。
- **HTML 邮件**：内嵌 HTML 目前使用 f-string 拼接姓名（[email_service.py:46](file:///Users/bytedance/Awake/backend/app/services/email_service.py#L46)），用户输入的 `student_name` 会直接进入 HTML；如允许用户自定义昵称含 `<`/`>` 需做 HTML 转义。MVP 阶段姓名长度上限 100，风险可控。
- **localStorage 明文存储**：前端把 access_token 和 student 对象明文存 `localStorage`（[client.js:27-29](file:///Users/bytedance/Awake/frontend/src/api/client.js#L27-L29)），存在 XSS 泄露风险；引入第三方脚本前必须评估。

## Known Pitfalls（已知陷阱）
- **SQLite 无迁移**：改 Column 后旧 `awaken.db` 会报错。本地开发：停服务→删除 `backend/awaken.db`→重启让 `create_all()` 重建。生产部署**必须**先引入 Alembic 再上线。
- **DeerFlow mock 降级会被误判为"接口坏了"**：当 `DEERFLOW_ENABLED=true` 但 DeerFlow 没启动时，接口 200 但 `mode=mock`，前端不会报错。排查对话质量问题时先看后端日志里有没有 "DeerFlow chat 调用失败，降级到 mock"。
- **DeerFlow 非 OpenAI**：不要尝试把 `base_url` 塞给 openai SDK，会 404。
- **CORS_ORIGINS 是 JSON 字符串**：`.env` 里写 `BACKEND_CORS_ORIGINS=["http://a","http://b"]`，**不要**用逗号分隔字符串，否则会走到 fallback 默认值。
- **前端 API baseURL 是 `/api`**：[client.js:4](file:///Users/bytedance/Awake/frontend/src/api/client.js#L4) 相对路径依赖 Vite 代理；生产部署必须在反向代理层把 `/api` 转发到后端 8000，或改成绝对 URL。
- **聊天消息的空白换行**：AI 回复有多段文本时，气泡必须支持 `white-space: pre-wrap`（当前已在 CSS 设置，重构样式时不要丢）。
- **测试 DB 清理**：[conftest.py:35](file:///Users/bytedance/Awake/backend/tests/conftest.py#L35) 每个用例后 `drop_all`，如果新增测试里手动建连接/会话，记得关闭否则 SQLite 文件锁可能导致下一个用例失败。
- **Feishu task_created 当前始终走 mock 日志**：[feishu_service.py:97-98](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py#L97-L98) 没有调用 `_send_webhook`（目前只生成卡片 payload 并打日志）。真要推飞书需补 webhook URL 字段 + `_send_webhook` 调用。
- **Task.feedback 字段已确认使用**：[CheckIn.jsx:72-75](file:///Users/bytedance/Awake/frontend/src/pages/CheckIn.jsx#L72-L75) 会把 textarea 内容（空串转 null）传给 `/api/task-complete`。
- **Login.jsx Navbar variant 错误**：[Login.jsx:52](file:///Users/bytedance/Awake/frontend/src/pages/Login.jsx#L52) 目前用 `<Navbar />`（默认 marketing variant），导致登录页显示营销导航和"立即注册"按钮，应该与 Chat/Success/CheckIn 一致使用 `<Navbar variant="app" />`。这是已知不一致，未来改 Login 页时顺手修正。
- **补鉴权的兼容性**：给业务接口加 `Depends(get_current_student)` 时，注意邮件链接 `/chat?email=...` 的旧用户首次进来没 token，需要决策：(a) 先让前端凭 email 调一次 login 换 token 再进入；(b) 保持 email 链接作为"无 token 入口"但后端做频率/签名限制；(c) 废弃 email 链接统一走登录。选定前不要直接加 Depends 让邮件链接 401。
- **登录无密码≠无鉴权**：当前 `/api/login` 只要邮箱已注册就签发 token，等价于"知道邮箱即可登录"。在产品决定加强身份前，不要把 Student 表扩展为可承载敏感数据的账号系统。
