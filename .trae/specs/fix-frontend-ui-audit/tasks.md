# Tasks

- [x] Task 1: 建立最小视觉基础并修复全局可访问性：扩展 `global.css` 的语义 token，统一核心按钮/表单/卡片/排版尺度，增加焦点样式、`prefers-reduced-motion`、`100dvh` 与移动端安全区；不新增依赖。
  - [x] SubTask 1.1: 增加颜色、文字、表面、边框、状态、圆角、阴影和字号 token
  - [x] SubTask 1.2: 将 Workspace 与 Chat 的 `100vh` 改为动态视口兼容写法
  - [x] SubTask 1.3: 增加全局 `:focus-visible` 和 reduced-motion 降级
  - [x] SubTask 1.4: 清理本次涉及页面的 inline style，复用语义 class

- [x] Task 2: 完善 Landing 与认证转化路径：补齐真实 Landing sections、移除空链接、统一 CTA；重构 Register/Login/Success 的布局和文案，确保注册提交按钮在 1366×768 首屏可见。
  - [x] SubTask 2.1: Landing 增加工作原理、小海体验、微行动、信任说明和最终 CTA
  - [x] SubTask 2.2: Navbar 只保留真实导航目标
  - [x] SubTask 2.3: Register/Login 使用统一认证布局并压缩桌面垂直密度
  - [x] SubTask 2.4: Success 保留唯一主 CTA 进入 `/app/chat`，演示入口退出真实主流程

- [x] Task 3: 收敛学生工作台信息架构：从 Sidebar 移除能力入口，简化 ContextBar 和 Settings 的工程术语，保留 `/app/capabilities` 作为隐藏内部调试路由。
  - [x] SubTask 3.1: Sidebar 收敛为对话、微行动、设置
  - [x] SubTask 3.2: ContextBar 只展示学生身份与小海状态
  - [x] SubTask 3.3: Settings 改为学生可理解的账户与可用性表达
  - [x] SubTask 3.4: 直接访问 `/app/capabilities` 仍可使用

- [x] Task 4: 将打卡并入 Workspace：新增 `/app/checkin` 子路由，改造 CheckIn 为 Outlet 视图，更新任务和对话跳转，并保留旧 `/checkin`、`/checkin/demo` 查询参数兼容重定向。
  - [x] SubTask 4.1: App.jsx 增加 `/app/checkin` 并实现旧路由重定向
  - [x] SubTask 4.2: CheckIn 移除独立 Navbar，采用工作台状态/表单样式
  - [x] SubTask 4.3: Tasks 与 Chat 的打卡跳转统一到 `/app/checkin`
  - [x] SubTask 4.4: 打卡页在 Sidebar 中归属微行动高亮

- [x] Task 5: 修复关键异步状态：Chat 增加分阶段长等待、取消等待和失败重试；Tasks 使 loading、未登录、error、empty、data 严格互斥。
  - [x] SubTask 5.1: Chat 使用现有 Axios 请求能力实现取消或忽略过期响应
  - [x] SubTask 5.2: Chat 在 5 秒、15 秒切换可理解等待文案
  - [x] SubTask 5.3: Chat 请求失败后提供重试刚才消息
  - [x] SubTask 5.4: Tasks error 分支阻止空态同时渲染，并提供恢复动作

- [x] Task 6: 文案与 CTA 自检：统一学生端称谓、主动作和错误提示，确保每页只有一个主要意图，不在学生路径展示 gateway/provider/skill/assistant_id 等工程词。

- [x] Task 7: 静态验证与构建：检查空链接、旧 `100vh`、缺失 reduced-motion、学生导航工程术语和涉及页面 inline style；运行 `npm run build`。
  - [x] SubTask 7.1: 使用 `rg` 检查 `href="#"`、无目标锚点和工程术语
  - [x] SubTask 7.2: 使用 `rg` 检查 `100vh`、inline style 和 reduced-motion
  - [x] SubTask 7.3: 运行前端生产构建

- [x] Task 8: 浏览器端到端验证：在桌面与移动视口验证 Landing、注册、登录、成功页、工作台对话、任务错误/空态、打卡路由、隐藏能力页、减少动态效果和关键键盘焦点。
  - [x] SubTask 8.1: 桌面 1366×768 验证 Landing 与注册首屏
  - [x] SubTask 8.2: 移动 390×844 验证 Landing、注册、工作台抽屉和聊天输入区
  - [x] SubTask 8.3: 验证 `/chat`、`/checkin`、`/checkin/demo` 兼容重定向保留查询参数
  - [x] SubTask 8.4: 验证任务 error/empty 互斥、聊天等待/取消/重试
  - [x] SubTask 8.5: 检查浏览器控制台无新增 error

- [x] Task 9: Ponytail 最终审查：检查是否新增无调用代码、重复 helper、第三方依赖、无依据兜底或 UI 症状补丁；删除非必要改动并复跑构建。

- [x] Task 10: 修复独立审查发现的问题：建立 Chat 邮箱身份边界，避免旧请求/消息串入新用户；区分小海降级与服务不可达；补齐打卡导航和聊天输入无障碍语义；删除无效 prop；收敛 CSS 重复覆盖。
  - [x] SubTask 10.1: queryEmail 改变时中止活动请求、失效 requestId，并重置消息、提炼态、失败态和欢迎状态
  - [x] SubTask 10.2: Workspace 状态源区分 online、degraded、unreachable，学生文案不做无法保证的“基础模式可用”承诺
  - [x] SubTask 10.3: `/app/checkin` 对“微行动”设置 `aria-current="page"`，Chat textarea 增加稳定可访问名称
  - [x] SubTask 10.4: 删除 ContextBar 无效 `currentModel` prop
  - [x] SubTask 10.5: 合并 global.css 中重复的 checkin/settings/chat-input/button 规则，保持视觉不回退
  - [x] SubTask 10.6: 复跑构建、静态检查和相关浏览器回归

- [x] Task 11: 完成异步身份边界闭环：修复无 email 与 StrictMode 初始化时序、任务提炼跨身份响应、Chat 草稿残留、CheckIn 查询参数快速切换竞态，并删除剩余重复 CSS selector。
  - [x] SubTask 11.1: 使用稳定 identity key，仅在身份实际变化时重置 Chat，移除 email 时立即阻止旧身份欢迎请求
  - [x] SubTask 11.2: 任务提炼请求绑定身份与请求序号，身份改变后旧结果不得跳转
  - [x] SubTask 11.3: 身份改变时清空 input/toast/extracting 等全部会话级状态
  - [x] SubTask 11.4: CheckIn 参数变化时失效旧请求并同步重置 loading/task/error/completed/feedback
  - [x] SubTask 11.5: 合并重复 `.settings-grid` selector
  - [x] SubTask 11.6: 复跑静态、浏览器和 Ponytail 验证

- [x] Task 12: 解决最终复核缺口：为 Chat 增加“当前路由身份已解析”闸门，避免 effect 闭包使用旧身份；使用不会被 NavLink 覆盖的当前页语义；使 `.settings-grid` 仅有一个 selector 定义。
  - [x] SubTask 12.1: 欢迎请求仅在当前 routeIdentityKey 已完成身份解析后触发
  - [x] SubTask 12.2: `/app/checkin` 的微行动链接在真实 DOM 中具有 `aria-current="page"`
  - [x] SubTask 12.3: `.settings-grid` 的布局属性合并到单一 selector 块
  - [x] SubTask 12.4: 最终静态、浏览器和 Ponytail 验证

# Task Dependencies

- Task 1 是共享视觉基础，Task 2、Task 4、Task 5 的样式收尾依赖 Task 1。
- Task 2 与 Task 3 可并行。
- Task 4 依赖 Task 3 的 Sidebar 信息架构。
- Task 5 与 Task 2、Task 3 可并行实现逻辑，但最终样式依赖 Task 1。
- Task 6 依赖 Task 2、Task 3、Task 4、Task 5。
- Task 7 依赖 Task 1-6。
- Task 8 依赖 Task 7 构建通过。
- Task 10 依赖 Task 8 的独立验证发现。
- Task 11 依赖 Task 10 的第二轮独立验证发现。
- Task 12 依赖 Task 11 的最终复核发现。
- Task 9 依赖 Task 12。
