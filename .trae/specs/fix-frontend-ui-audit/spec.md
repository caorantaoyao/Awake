# Awaken 前端 UI 审计全量修复 Spec

## Why

当前前端已经具备营销页、注册登录、对话工作台、任务与打卡闭环，但审计确认存在无效导航、注册 CTA 首屏不可见、学生端暴露开发者控制台、长等待反馈不足、错误与空态混杂、页面体系割裂等问题。此次变更以学生真实使用路径为中心，在不引入新依赖、不重写现有架构的前提下修复审计报告中的全部 12 项问题。

## Design Direction

- **Purpose**：帮助高中生从“了解产品”顺畅进入“小海对话”，再完成微行动和打卡。
- **Tone**：克制、清晰、温和的教育科技体验；保留蓝色品牌资产，减少开发者控制台感。
- **Differentiation**：以“小海陪伴式对话 → 当天可完成微行动”为核心记忆点，而不是模型、skills 或工程参数。
- **Constraints**：
  - 复用 React 18、React Router、Axios 与现有手写 CSS。
  - 不新增 UI 库、状态管理库、字体包或动画依赖。
  - 不修改 `deer-flow/`。
  - 不改变后端接口契约。
  - 保留 `/chat`、`/checkin` 等旧链接兼容。
  - 所有可访问性、键盘操作、减少动态效果和移动端安全区要求不可削减。

## Ponytail Decision

- L1 YAGNI：审计问题全部出现在现有用户路径，必须修复；不新增“成长记录”等尚无数据支撑的页面。
- L2 复用代码库：复用 `WorkspaceLayout`、`Navbar`、`Sidebar`、`ContextBar`、现有路由与表单组件样式。
- L3 标准能力：使用 CSS variables、媒体查询、React 本地状态和 React Router 重定向。
- L4 原生平台：使用 `prefers-reduced-motion`、`100dvh`、`env(safe-area-inset-bottom)`、语义 HTML。
- L5 已装依赖：只使用现有依赖，不增加第三方包。
- 最终落点：L6/L7，优先共享样式和源头状态分支修复，避免页面级重复补丁。

## What Changes

- 完善 Landing 信息架构，补齐所有真实导航目标，删除空链接，形成 Hero、工作原理、小海体验、微行动示例、信任说明和最终 CTA。
- 重构注册与登录页的认证布局，使桌面注册提交按钮在 1366×768 首屏可见，并统一 CTA 文案。
- 将学生工作台主导航收敛为“对话、微行动、设置”，隐藏 DeerFlow 能力控制入口；能力页路由保留为内部调试入口。
- 将打卡页纳入 `WorkspaceLayout`，新增 `/app/checkin`，旧 `/checkin` 与 `/checkin/demo` 保留查询参数并重定向。
- 简化 `ContextBar` 的学生端信息，移除模型和工程术语；学生只看到身份和“小海状态”。
- 为聊天长等待增加分阶段解释、可取消本次等待、失败后重试；不修改后端协议。
- 修复任务页状态优先级，使 loading、未登录、error、empty、data 互斥。
- 建立最小 CSS 语义 token，统一按钮、表单、卡片、状态与排版尺度，清理本次涉及页面的 inline style。
- 增加 `prefers-reduced-motion`、`100dvh`、移动端安全区与焦点可见样式。
- 收敛学生端文案和 CTA，使每页只有一个明确主动作。

## Impact

- Affected specs:
  - 营销页信息架构与转化
  - 注册/登录体验
  - Workspace 学生导航
  - 对话长等待与错误恢复
  - 任务状态呈现
  - 打卡路由与布局
  - 设计 token、响应式和可访问性
- Affected code:
  - `frontend/src/App.jsx`
  - `frontend/src/components/Navbar.jsx`
  - `frontend/src/components/Sidebar.jsx`
  - `frontend/src/components/ContextBar.jsx`
  - `frontend/src/layouts/WorkspaceLayout.jsx`
  - `frontend/src/pages/Landing.jsx`
  - `frontend/src/pages/Register.jsx`
  - `frontend/src/pages/Login.jsx`
  - `frontend/src/pages/Success.jsx`
  - `frontend/src/pages/Chat.jsx`
  - `frontend/src/pages/Tasks.jsx`
  - `frontend/src/pages/CheckIn.jsx`
  - `frontend/src/pages/Settings.jsx`
  - `frontend/src/styles/global.css`
- 不受影响：
  - 后端接口和数据库
  - DeerFlow 外部仓库
  - `Capabilities.jsx` 的内部调试功能本身

## ADDED Requirements

### Requirement: 完整可信的 Landing 信息架构

系统 SHALL 提供完整 Landing 页面，所有导航和 CTA 均指向真实内容或真实路由，并以克制、可信的教育科技视觉呈现 Awaken 的“对话到行动”价值。

#### Scenario: 点击营销导航

- **WHEN** 用户点击产品原理、小海体验、微行动或信任说明导航
- **THEN** 页面平滑定位到对应真实区块，不出现空链接或无反馈

#### Scenario: 完成首屏阅读

- **WHEN** 用户在 1366×768 桌面视口打开 Landing
- **THEN** H1、价值描述、主 CTA 和核心图片均在首屏内，主 CTA 文案为明确的“开始和小海对话”

#### Scenario: 查看首屏以下内容

- **WHEN** 用户继续向下滚动
- **THEN** 可看到产品工作流程、小海对话示例、微行动示例、信任边界和最终 CTA

### Requirement: 高转化认证布局

系统 SHALL 使用统一认证布局承载注册和登录，使主要表单动作在常见桌面视口内可见，并保持移动端单列可读。

#### Scenario: 桌面注册

- **WHEN** 用户在 1366×768 视口打开 `/register`
- **THEN** 注册标题、全部字段和提交按钮在首屏内可见

#### Scenario: 移动端注册

- **WHEN** 用户在 390×844 视口打开 `/register`
- **THEN** 页面为单列布局，字段间距适中，键盘和滚动不遮挡提交动作

### Requirement: 学生目标导向的工作台

系统 SHALL 让普通学生只看到与对话、微行动和账户状态有关的导航与信息，不暴露 DeerFlow skills、provider、assistant_id、模型列表等工程术语。

#### Scenario: 学生查看侧边栏

- **WHEN** 用户进入任意 `/app/*` 学生页面
- **THEN** 侧边栏不显示“能力 DeerFlow”，只保留学生目标相关入口

#### Scenario: 内部调试访问能力页

- **WHEN** 开发者直接访问 `/app/capabilities`
- **THEN** 能力控制页仍可使用，但不从学生主导航暴露

#### Scenario: 查看上下文栏

- **WHEN** 用户进入工作台
- **THEN** 上下文栏展示学生身份和“小海状态”，不展示模型名、gateway 或 provider

### Requirement: 连续的对话到打卡工作区

系统 SHALL 将 CheckIn 纳入 WorkspaceLayout，并保持旧链接兼容。

#### Scenario: 从任务进入打卡

- **WHEN** 用户从任务页点击“去打卡”
- **THEN** 导航至 `/app/checkin?task_id=<id>`，侧边栏和上下文栏仍可见

#### Scenario: 旧打卡链接

- **WHEN** 用户访问 `/checkin` 或 `/checkin/demo` 并携带查询参数
- **THEN** 系统保留查询参数并重定向到对应 `/app/checkin` 路径

### Requirement: 可理解的长等待状态

系统 SHALL 将 DeerFlow 的长响应作为一等状态处理，为用户提供分阶段说明、取消等待和失败重试。

#### Scenario: 响应等待超过 5 秒

- **WHEN** 对话请求尚未完成且等待超过 5 秒
- **THEN** 界面显示比“正在思考”更具体的说明

#### Scenario: 响应等待超过 15 秒

- **WHEN** 对话请求尚未完成且等待超过 15 秒
- **THEN** 界面说明本次分析较深入，并提供“取消等待”动作

#### Scenario: 请求失败

- **WHEN** 对话请求失败
- **THEN** 页面保留用户消息，展示可理解的失败说明和“重试刚才消息”动作

#### Scenario: 用户取消等待

- **WHEN** 用户点击取消等待
- **THEN** 前端取消或忽略当前请求结果、恢复输入能力，不写入伪造回复

### Requirement: 互斥的任务状态

系统 SHALL 按 loading、未登录、error、empty、data 的顺序互斥展示任务页状态。

#### Scenario: 任务接口失败

- **WHEN** 任务同步失败
- **THEN** 只展示错误说明和恢复动作，不同时展示“还没有任务”空态

#### Scenario: 任务为空

- **WHEN** 请求成功且任务数量为零
- **THEN** 展示空态和唯一主 CTA“去和小海聊聊”

### Requirement: 最小统一设计系统

系统 SHALL 使用全局 CSS variables 管理核心颜色、文字、表面、边框、状态、圆角、阴影和字号，并复用现有 class，禁止为本次修复引入 UI 组件库。

#### Scenario: 页面视觉一致

- **WHEN** 用户在 Landing、Register、Login、Workspace 和 CheckIn 之间切换
- **THEN** 主色、按钮、卡片、表单、标题和状态样式具有一致的品牌规则

### Requirement: 可访问且稳定的响应式体验

系统 SHALL 尊重减少动态效果偏好，使用动态视口单位并处理移动端安全区。

#### Scenario: 减少动态效果

- **WHEN** 系统设置 `prefers-reduced-motion: reduce`
- **THEN** 入场和循环动画被禁用或缩短，功能不受影响

#### Scenario: 移动端动态视口

- **WHEN** 移动端浏览器地址栏或键盘改变可用高度
- **THEN** 工作台和输入区基于 `100dvh` 保持稳定，底部安全区不遮挡输入

#### Scenario: 键盘导航

- **WHEN** 用户使用 Tab 键导航
- **THEN** 链接、按钮、输入框和侧栏控件具有清晰可见的焦点状态

## MODIFIED Requirements

### Requirement: Workspace 主导航

工作台主导航 SHALL 从“对话 / 任务 / 能力 / 设置”调整为“对话 / 微行动 / 设置”。能力页保留路由但不属于学生导航。

#### Scenario: 当前页面高亮

- **WHEN** 用户位于对话、任务、打卡或设置页面
- **THEN** 对应学生导航项高亮；打卡页归属“微行动”

### Requirement: 注册成功引导

注册成功页 SHALL 使用唯一主 CTA 引导用户进入 `/app/chat`，演示入口不在真实用户主流程中竞争注意力。

#### Scenario: 注册成功

- **WHEN** 注册接口成功并进入 `/success`
- **THEN** 页面主动作是“进入对话工作区”，返回首页为弱链接

### Requirement: 设置页表达

设置页 SHALL 以学生可理解语言展示小海可用性和账户信息；详细工程参数不作为学生页面主体。

#### Scenario: DeerFlow 离线

- **WHEN** DeerFlow 不可达
- **THEN** 学生看到“小海暂时不可用/会使用基础模式”等可理解说明，不看到 gateway 堆栈或 provider 信息

## REMOVED Requirements

### Requirement: 学生主导航中的能力控制入口

**Reason**：skills、模型和 gateway 属于内部调试能力，不符合高中生主流程目标，并且控制接口当前未鉴权。

**Migration**：保留 `/app/capabilities` 直接路由供内部联调，移除 Sidebar 入口和学生上下文中的工程参数。

### Requirement: Landing 空链接

**Reason**：`href="#"` 和不存在的锚点会破坏信任。

**Migration**：所有保留导航项改为真实 section id；无对应内容的入口直接删除。

### Requirement: CheckIn 独立 Navbar 布局

**Reason**：任务与打卡属于同一工作流，跳出 Workspace 会破坏连续性。

**Migration**：新增 `/app/checkin` 子路由；旧 `/checkin`、`/checkin/demo` 仅做兼容重定向。
