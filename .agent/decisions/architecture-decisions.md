# Decision: DeerFlow 作为外部引擎、本仓库只做 HTTP 编排

## Status
Accepted

## Context
- 原方案曾考虑直接集成飞书 Aily、或在本仓库内 embedding LLM 调用。
- DeerFlow 2.0 提供了完整的 super-agent harness（LangGraph、工具调用、记忆、多模型接入），且支持 `DEER_FLOW_AUTH_DISABLED=1` 零 key 本地启动。
- Awaken MVP 的核心价值不在模型/Agent 框架，而在「小海」人设 + 苏格拉底对话编排 + 微行动任务闭环。

## Decision
- `deer-flow/` 作为独立 clone 的外部引擎，通过 `.gitignore` 排除在本仓库外。
- 本仓库通过 HTTP 调用 DeerFlow 的 LangGraph 风格接口 `POST /api/runs/wait`（非 OpenAI 兼容）。
- 对话、工具、记忆、模型等能力归 DeerFlow；本仓库只负责 system prompt 组装、消息透传、回复解析、失败 mock 降级。

## Consequences
- 优点：关注点分离；DeerFlow 可以独立升级/换模型/开关工具而不影响 Awaken 业务代码；零 key 可用。
- 代价：本地开发需额外启动一个 DeerFlow 进程（:8001）；部署需协调两个服务。
- 约束：禁止在 Awaken 仓库内直接 import/openai SDK 调模型；禁止改 deer-flow 代码。

## Rejected Alternatives
- 直接在本仓库用 openai SDK 调 DeepSeek API：丢失 DeerFlow 的工具/记忆/agent 能力，且与后续 super-agent 规划背离。
- 把 deer-flow 作为 git submodule 纳入本仓库：增加耦合，DeerFlow 自身更新频繁，submodule 维护成本高于独立 clone。
- 走 OpenAI 兼容层（如 one-api）：DeerFlow 2.0 本身不是 OpenAI server 形态，套代理增加一层不必要复杂度。

---

# Decision: 两阶段互斥 prompt（探索期 / 解锁期）

## Status
Accepted

## Context
- 早期把"多提问少给建议"和"主动给建议/调用工具/生成任务"的规则塞进同一个 system prompt，导致 DeepSeek 在权重冲突时拒绝给建议（即"解锁指令不生效"）。

## Decision
- `XIAOHAI_EXPLORE_PROMPT`（探索期）与 `XIAOHAI_UNLOCK_PROMPT`（解锁期）**互斥二选一**注入。
- 阈值由 `XIAOHAI_UNLOCK_AFTER_TURNS` 控制（当前 = 3），后端根据 user 轮数选择一段拼接到 `XIAOHAI_PERSONA_PROMPT` 之后。
- 阈值必须与 `/api/chat` 中 `can_extract_task` 的轮次判断严格一致。

## Consequences
- 前 2 轮小海只追问，不直接给结论；第 3 轮起主动给建议、允许联网搜索、可生成微行动。
- 前端 `can_extract` 显示"接受今天的微行动任务"卡片的时机与解锁期同步。

## Rejected Alternatives
- 一段 prompt 里用 "前 N 轮……之后……" 的自然语言描述：对小模型不稳定，容易不遵守。
- 在前端做阶段切换：把 prompt 编排分散到前后端两处，违反单一事实源。

---

# Decision: Navbar 双 variant（marketing / app）

## Status
Accepted（已被 WorkspaceLayout 部分取代，保留用于非 Workspace 页面）

## Context
- 早期所有页面共用同一个 Navbar，导致 Chat/CheckIn 等内部页面出现"立即注册/登录"按钮和指向不存在锚点（#how-it-works 等）的营销链接，交互自相矛盾。

## Decision
- Navbar 组件通过 `variant` prop 区分两类页面：
  - `variant="marketing"`（默认）：完整导航 + 注册/登录按钮，用于 Landing 页。
  - `variant="app"`：只保留 Logo（链接回 `/`），隐藏所有营销导航与转化按钮，用于 Success/CheckIn 等非 Workspace 内部功能页。
- `/app/*` Workspace 内页不再使用 Navbar，改用 WorkspaceLayout（Sidebar + ContextBar）。

## Consequences
- 营销转化路径与应用内路径视觉/交互隔离。
- Register/Login/Success 使用 app variant；CheckIn 已迁入 WorkspaceLayout。

---

# Decision: 引入密码系统（PBKDF2_SHA256）

## Status
Accepted

## Context
- 早期登录仅校验邮箱存在即签发 JWT（等同于"知道邮箱即可登录"），存在身份冒用风险。
- 产品需要在进入正式测试前补上基本的账号安全。

## Decision
- 使用 PBKDF2_SHA256 + 随机盐做密码哈希，迭代次数 260,000（符合 OWASP 2024 最低推荐）。
- 注册必须传密码（min_length=8），登录必须验证密码哈希。
- 新增 `password_hash` 列（String(255)，nullable=True 以兼容旧数据）。
- 迁移机制：init_db 时自动执行 `migrate_password_hashes()`，对 `password_hash IS NULL` 的旧行用 `AUTH_LEGACY_USER_DEFAULT_PASSWORD` 回填（幂等，不覆盖已有 hash）。

## Consequences
- 旧库升级无破坏性：已有用户可用默认密码登录，登录后应引导改密。
- 密码格式为 `$pbkdf2-sha256$iterations$salt_b64$hash_b64$`（兼容 passlib 风格）。
- `verify_password` 对无效 hash 格式返回 False 而非抛异常，避免拒绝服务。
- 邮件链接 `/app/chat?email=...` 不再能仅凭邮箱进入——需要决策 Magic Link 方案或废弃邮件 CTA。

## Rejected Alternatives
- bcrypt/argon2：需要额外 C 依赖，在 Python:3.11-slim Docker 镜像中编译成本高；PBKDF2 用标准库 hashlib 即可实现，零依赖。
- 不做迁移、强制旧用户重新注册：体验差；MVP 阶段默认密码回填已足够。

---

# Decision: Workspace 布局架构（Sidebar + ContextBar + Outlet）

## Status
Accepted

## Context
- 早期所有页面都是独立路由，没有共享的工作区外壳。随着功能增长（任务列表、能力控制、设置），每个页面重复实现导航/状态拉取/上下文展示会导致代码重复和状态不一致。

## Decision
- 引入 `/app` 前缀子路由，所有工作区内页通过 [WorkspaceLayout.jsx](file:///Users/bytedance/Awake/frontend/src/layouts/WorkspaceLayout.jsx) 外壳渲染。
- WorkspaceLayout 由三部分组成：
  - [Sidebar.jsx](file:///Users/bytedance/Awake/frontend/src/components/Sidebar.jsx)：学生导航（今日/对话/微行动/探索/成长，设置置底），支持折叠与移动端抽屉。
  - [ContextBar.jsx](file:///Users/bytedance/Awake/frontend/src/components/ContextBar.jsx)：顶部上下文栏，显示当前区域标题、学生信息与面向学生的小海可用状态。
  - `<Outlet />`：子页面渲染区，通过 React Router Outlet context 透传共享状态。
- 学生 Workspace 不请求受限的 DeerFlow 控制接口，使用固定的按需连接状态。
- 共享状态通过 Outlet context 透传：`{student, deerflowStatus, currentModel, setStudent, refreshDeerflowStatus}`。

## Consequences
- 工作区内页无需重复包 Navbar 或请求控制面板状态。
- 新增工作区页面只需：建 page 组件 → 加 Route → Sidebar 加导航项 → ContextBar 加 SECTION_TITLES 映射。
- 非工作区页面（Landing/Register/Login/Success）仍走顶层路由 + Navbar variant 模式；旧 CheckIn 路径重定向到 Workspace。
- `/chat` 旧路径重定向到 `/app/chat` 保留 query string 兼容邮件链接。

## Rejected Alternatives
- 用 CSS 媒体查询 + 全局状态做自适应：React Router 嵌套路由是更声明式的方案，与现有架构吻合。
- 引入状态管理库（Zustand/Redux）共享状态：MVP 阶段 Outlet context 已够用，不需要额外依赖。

---

# Decision: DeerFlow 控制面板（代理 status/skills/models）

## Status
Accepted

## Context
- DeerFlow 加载了多个 skill（联网搜索等），开发/调试时需要快速查看引擎状态、开关 skill、确认模型列表。
- 前端不应直接访问 DeerFlow :8001（跨域、耦合、安全风险）。

## Decision
- 后端新增 [deerflow_control.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_control.py) 作为 DeerFlow gateway 的控制代理，封装 4 个方法：`get_status` / `list_skills` / `set_skill_enabled` / `list_models`。
- 每个方法内部做归一化（`_normalize_skills` / `_normalize_models`），把 DeerFlow 原始返回映射到稳定 schema，并保留 `raw` 字段透传原始数据（`ConfigDict(extra="allow")`）。
- 所有控制接口必须有降级：httpx 异常时返回 `online: false` + error 字段，不抛 500。
- [Capabilities.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Capabilities.jsx) 保留为内部联调代码；学生路由 `/app/capabilities` 重定向到今日页。[Settings.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Settings.jsx) 只展示学生资料与 API 健康检查。
- 控制接口超时独立配置（`DEERFLOW_CONTROL_TIMEOUT_SECONDS=60`），不与对话接口 120s 混用。

## Consequences
- 内部联调代码仍可复用归一化后的控制 API。
- 普通学生通过 `deny_student_control_access` 固定收到 403，不能查看模型或开关 skill。
- 学生 ContextBar 只表达产品可用状态，不暴露模型、Gateway 等工程术语。

## Rejected Alternatives
- 前端直接调 DeerFlow :8001：违反"所有 DeerFlow 调用经后端编排"原则，跨域配置复杂。
- 不做归一化直接透传：DeerFlow 返回格式可能变化，归一化层提供稳定契约，前端不依赖 DeerFlow 内部结构。

---

# Decision: Docker 化部署（backend + frontend 双镜像）

## Status
Accepted

## Context
- 本地开发用 uvicorn + Vite dev server，但需要可移植的部署形态。

## Decision
- Backend Dockerfile：基于 python:3.11-slim，安装依赖，暴露 8000，HEALTHCHECK 调 `/api/health`。
- Frontend Dockerfile：多阶段构建（node:20-alpine 构建 → nginx:1.27-alpine 托管）。
- Nginx 配置：SPA fallback（`try_files $uri /index.html`）+ `/api/` 反向代理到 `backend:8000`，`proxy_read_timeout 130s` 与前端超时对齐。

## Consequences
- 可通过 docker-compose 一键启动 backend + frontend + deer-flow 三服务。
- 前端 nginx 反向代理避免了生产环境 CORS 配置复杂度。
- nginx proxy_read_timeout 必须与 Vite proxy 超时保持一致（130s），改时同步。
