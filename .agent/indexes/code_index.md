# Code Index

面向未来 agent 的代码地图：遇到关键词先查这里，再打开文件。

## Entry Points
| Area | Path | Notes |
| --- | --- | --- |
| Backend bootstrap | [backend/main.py](file:///Users/bytedance/Awake/backend/main.py) | FastAPI app 实例、CORS、startup hook、uvicorn 入口 |
| HTTP routes | [backend/app/api/routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | 所有 `/api/*` 端点一文件集中管理 |
| Config / env / prompts | [backend/app/core/config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) | Settings 单例；JWT 密钥/有效期、小海人设/阶段 prompt/阈值全部在这里 |
| JWT 工具 | [backend/app/services/auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py) | `create_access_token` / `decode_access_token`，基于 python-jose |
| 鉴权依赖 | [backend/app/api/routes.py:35-60](file:///Users/bytedance/Awake/backend/app/api/routes.py#L35-L60) | `get_current_student` 依赖 + HTTPBearer；当前仅 `/api/auth/me` 挂载 |
| DB engine & session | [backend/app/core/database.py](file:///Users/bytedance/Awake/backend/app/core/database.py) | `Base`, `get_db()`, `init_db()`；SQLite 专用 `check_same_thread=False` |
| ORM models | [backend/app/models/models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) | `Student`, `Task`, `GradeEnum`, `TaskStatusEnum` |
| Pydantic schemas | [backend/app/schemas/schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) | 请求/响应契约，与 models 解耦 |
| DeerFlow adapter | [backend/app/services/deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | LangGraph 协议适配、system prompt 组装、mock 降级、回复解析 |
| Email service | [backend/app/services/email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) | SMTP 发送 + HTML 邮件模板，关闭时 mock |
| Feishu webhook | [backend/app/services/feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) | 注册/打卡/任务卡片 webhook，best-effort |
| Tests | [backend/tests/](file:///Users/bytedance/Awake/backend/tests) | pytest；[conftest.py](file:///Users/bytedance/Awake/backend/tests/conftest.py) 强制隔离外部服务；[test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) 覆盖所有端点 |
| Frontend bootstrap | [frontend/src/main.jsx](file:///Users/bytedance/Awake/frontend/src/main.jsx) → [index.html](file:///Users/bytedance/Awake/frontend/index.html) | React 挂载点 |
| Frontend routes | [frontend/src/App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) | SPA 路由表 |
| API client | [frontend/src/api/client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) | axios 实例；token localStorage 存取；请求拦截器自动带 Authorization；chat/extract-task 超时 130s |
| Navbar | [frontend/src/components/Navbar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Navbar.jsx) | `variant="marketing"|"app"` 双模式 |
| Pages | [frontend/src/pages/](file:///Users/bytedance/Awake/frontend/src/pages) | Landing / Register / Login / Success / Chat / CheckIn |
| Styles | [frontend/src/styles/global.css](file:///Users/bytedance/Awake/frontend/src/styles/global.css) | 全局样式单文件 |
| Vite config | [frontend/vite.config.js](file:///Users/bytedance/Awake/frontend/vite.config.js) | dev port=3000；`/api` → `:8000` proxy；超时 130s |
| Static landing | [frontend/landing.html](file:///Users/bytedance/Awake/frontend/landing.html) | 独立静态页（未接入 SPA 路由，`Needs verification` 是否在用） |

## Keyword Routing
| Product/code keyword | Start here | Then check | Notes |
| --- | --- | --- | --- |
| 注册、register、signup | [routes.py:63](file:///Users/bytedance/Awake/backend/app/api/routes.py#L63-L113) | [pages/Register.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Register.jsx), email_service | 重复邮箱返回 400 |
| 登录、login、JWT、token、鉴权、auth | [routes.py:116](file:///Users/bytedance/Awake/backend/app/api/routes.py#L116-L144) | [auth_service.py](file:///Users/bytedance/Awake/backend/app/services/auth_service.py), [pages/Login.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Login.jsx), [client.js:11-43](file:///Users/bytedance/Awake/frontend/src/api/client.js#L11-L43) | 当前仅邮箱存在即签发；业务接口大多未挂 Depends(get_current_student) |
| get_current_student、Bearer、Authorization | [routes.py:35-60](file:///Users/bytedance/Awake/backend/app/api/routes.py#L35-L60) | HTTPBearer 依赖；加鉴权时参考 `/api/auth/me` | — |
| 任务、task、微行动 | [models.py:33](file:///Users/bytedance/Awake/backend/app/models/models.py#L33-L46) | routes.py `/api/tasks*`, CheckIn.jsx | 状态机：进行中/已完成/已过期 |
| 打卡、check-in、complete | [routes.py:192](file:///Users/bytedance/Awake/backend/app/api/routes.py#L192-L241) | CheckIn.jsx, feishu_service `notify_task_complete` | 幂等：已完成直接返回 |
| 对话、chat、小海、Socratic | [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | [Chat.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Chat.jsx), config.py `XIAOHAI_*` | 非 OpenAI 协议；mock 兜底 |
| DeerFlow、LangGraph、assistant | [deerflow_service.py:42-66](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L42-L66) | config.py `DEERFLOW_*` | `/api/runs/wait`，thread_id 随机 |
| 联网搜索、工具调用、web_search | 外部 `deer-flow/` 仓库 | config.yaml（deer-flow 侧，已 gitignore） | 本仓库不处理工具开关 |
| prompt、人设、苏格拉底、探索期/解锁期 | [config.py:34-55](file:///Users/bytedance/Awake/backend/app/core/config.py#L34-L55) | [deerflow_service.py:31-40](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L31-L40) | 两段 prompt 互斥二选一，阈值=3 |
| can_extract_task、提炼任务 | [routes.py:271-272](file:///Users/bytedance/Awake/backend/app/api/routes.py#L271-L272), [Chat.jsx:239-255](file:///Users/bytedance/Awake/frontend/src/pages/Chat.jsx#L239-L255) | `/api/chat/extract-task` | 轮次≥3 时出现 |
| 超时、timeout | [client.js:80-90](file:///Users/bytedance/Awake/frontend/src/api/client.js#L80-L90), [vite.config.js:13-14](file:///Users/bytedance/Awake/frontend/vite.config.js#L13-L14), [deerflow_service.py:58](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L58) | 三处必须保持：前端 130s ≥ Vite proxy 130s ≥ httpx 120s | |
| CORS、跨域 | [main.py:21-27](file:///Users/bytedance/Awake/backend/main.py#L21-L27), [config.py:58-69](file:///Users/bytedance/Awake/backend/app/core/config.py#L58-L69) | vite proxy（开发） | 部署要更新 `BACKEND_CORS_ORIGINS` |
| 邮件、SMTP、欢迎邮件、CTA | [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) | config.py `SMTP_*`, `FRONTEND_URL` | HTML 模板内嵌；关闭时仅记日志 |
| 飞书、webhook、卡片 | [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) | config.py `FEISHU_*` | best-effort，失败不抛 |
| 导航、Navbar、登录/注册按钮 | [Navbar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Navbar.jsx) | App.jsx 各页面 | 内页必须 `variant="app"` |
| 数据库、SQLite、awaken.db | [database.py](file:///Users/bytedance/Awake/backend/app/core/database.py) | models.py, DATABASE_URL | 无迁移；删 db 会丢数据 |
| 测试、pytest、TestClient | [conftest.py](file:///Users/bytedance/Awake/backend/tests/conftest.py), [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) | 独立 test_awaken.db；强制 SMTP/DeerFlow mock | 跑前确保 backend 根目录可写 |

## Common Investigation Paths
### 加或改一个返回字段
1. 改 [models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) Column（注意 SQLite 无自动迁移，本地删 `awaken.db` 或手动 ALTER）
2. 改 [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) 对应 Response 字段
3. 若需要输入，改 Request schema
4. 检查路由是否需要赋值/返回该字段
5. 前端 [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) + 页面消费处
6. 跑 `pytest`；前端 `npm run build`

### 加或改对话/domain 逻辑
1. prompt 层：优先改 [config.py](file:///Users/bytedance/Awake/backend/app/core/config.py) 的 `XIAOHAI_*_PROMPT` 或阈值
2. 编排层（组装 messages、解析回复、mock）：改 [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py)
3. 触发条件/路由：改 [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) `/api/chat*`
4. 阈值一致性：`XIAOHAI_UNLOCK_AFTER_TURNS` == `can_extract_task` 判断中的 `>= 3`
5. 跑 `pytest tests/test_api.py::TestChatAPI tests/test_api.py::TestExtractTaskAPI`；本地走一次三用户轮对话验证

### 加或改一个外部通知
1. 参考 [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) / [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) 建 service 类，单例 `xxx_service = XxxService()`
2. Config 加 `XXX_ENABLED` + 开关字段，默认 `False`
3. 失败只 `logger.error` 并返回 False，**不要向上抛**
4. 在对应路由 `try/except` 块内调用
5. [conftest.py](file:///Users/bytedance/Awake/backend/tests/conftest.py) 里把该外部服务设为禁用，避免测试打外网

### 加一个 HTTP 接口
1. 在 [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) 加 Request/Response
2. 在 [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) 加 `@router`，写 `db` 依赖与错误码
3. 若调用 DeerFlow/外部服务：确保有 mock 降级
4. 前端 [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) 加方法；页面按需调用
5. 在 [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) 加 200/4xx 用例
6. 跑 `pytest`

### 加一个前端页面
1. 新建 `frontend/src/pages/Xxx.jsx`，导入并使用合适的 Navbar variant
2. [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) 加 `<Route>`
3. 营销/落地 → 默认 `variant="marketing"`；应用内功能页 → `variant="app"`
4. API 调用复用 [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js)
5. `npm run build` 验证

### 排查超时/长回复失败
1. 后端 httpx 超时：[deerflow_service.py:58](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py#L58)（120s）
2. Vite 代理超时：[vite.config.js:13-14](file:///Users/bytedance/Awake/frontend/vite.config.js#L13-L14)（130s）
3. 前端 axios 超时：[client.js:83-90](file:///Users/bytedance/Awake/frontend/src/api/client.js#L80-L90)（chat/extract-task 130s，其他 10s 默认）
4. 必须满足：前端 ≥ proxy ≥ httpx，不要只改一处

### 给业务接口补鉴权
1. 模板参考 [routes.py:142-144](file:///Users/bytedance/Awake/backend/app/api/routes.py#L142-L144)，给接口加 `current_student: Student = Depends(get_current_student)`
2. 把请求体里的 `student_email` 改为从 `current_student.email` 取，避免前端伪造
3. 前端拦截器 [client.js:37-43](file:///Users/bytedance/Awake/frontend/src/api/client.js#L37-L43) 已自动带 token，无需改前端请求
4. **兼容性决策**（先选再动）：
   - 保持 `/chat?email=...` 邮件链接可用 → 需在 Chat 页首次进入时用 email 调 `/api/login` 换 token 再继续
   - 或废弃邮件链接统一要求登录 → 同步改 [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py) CTA、飞书卡片
5. 补 [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) 未带 token 返回 401 的用例
6. 跑 `pytest`；手动走"邮件链接直达"和"登录后进入"两条路径验证
