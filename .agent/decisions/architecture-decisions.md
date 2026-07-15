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
Accepted

## Context
- 早期所有页面共用同一个 Navbar，导致 Chat/CheckIn 等内部页面出现"立即注册/登录"按钮和指向不存在锚点（#how-it-works 等）的营销链接，交互自相矛盾。

## Decision
- Navbar 组件通过 `variant` prop 区分两类页面：
  - `variant="marketing"`（默认）：完整导航 + 注册/登录按钮，用于 Landing 页。
  - `variant="app"`：只保留 Logo（链接回 `/`），隐藏所有营销导航与转化按钮，用于 Chat/CheckIn/Success 等内部功能页。
- 所有新增内部功能页必须显式使用 `<Navbar variant="app" />`。

## Consequences
- 营销转化路径与应用内路径视觉/交互隔离，不会出现"在对话页点注册把自己踢出去"的问题。
- 未来若加真正的登录态，只需在 app variant 上加头像/退出，不影响营销页。

## Rejected Alternatives
- 为每个页面单独写导航：重复代码，改品牌要改 5 处。
- 用 CSS `display:none` 基于路由自动隐藏：路由路径和导航状态强耦合，加新页面容易漏。
