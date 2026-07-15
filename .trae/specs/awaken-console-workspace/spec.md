# Awaken 控制台工作台（类 Codex 布局）Spec

## Why
当前前端只有一个孤立的对话页 `/chat`，用户看到的是"一大片留白 + 一个聊天框"，既没有会话/项目管理，也没有 skill/模型等能力控制入口。DeerFlow 已经把这些能力通过 REST 暴露（`/api/skills`、`/api/models`、`/api/threads/*`），Awaken 后端也已有学生/任务数据，但前端完全没有承载面。本次借鉴 Codex/Claude Code 的"左侧导航 + 中间工作区 + 右侧上下文"三栏工作台布局，把散落的能力聚合成一个可操作的控制台。

## What Changes
- **BREAKING**：`/chat` 从独立整页改造为工作台内的一个工作区视图；对话页的 `Navbar` 在工作台内被左侧边栏取代（营销页 Navbar 不变）。
- 新增工作台外壳 `WorkspaceLayout`：左侧可折叠导航栏（对话 / 任务 / 能力 / 设置）+ 顶部上下文条（当前学生、DeerFlow 连接状态、当前模型）+ 中间路由出口。
- 新增「任务管理」视图：列出当前学生的全部微行动任务（进行中/已完成/已过期），支持查看详情、跳转打卡；数据来自 Awaken 已有的 `GET /api/students/{email}`。
- 新增「能力控制」视图：展示 DeerFlow 已加载的 skills 与可用模型，支持开关 skill、查看当前对话引擎状态；数据来自新增的 Awaken 后端代理接口（转发 DeerFlow `/api/skills`、`/api/models`、`PUT /api/skills/{name}`）。
- 新增「设置/关于」视图：展示 DeerFlow 连接、模型、阶段切换阈值等只读运行信息 + 健康检查。
- 新增后端「DeerFlow 控制代理」：Awaken 后端新增 `/api/deerflow/skills`、`/api/deerflow/skills/{name}`（PUT）、`/api/deerflow/models`、`/api/deerflow/status`，转发到本地 DeerFlow gateway，隔离鉴权与不可达降级。
- 对话视图（原 Chat）保留全部现有能力（多轮、阶段切换、接受任务），仅改为嵌入工作区、可复用会话上下文条。

## Impact
- Affected specs: 前端信息架构、对话入口、任务链路、DeerFlow 能力可见性
- Affected code:
  - 新增 `frontend/src/layouts/WorkspaceLayout.jsx`、`frontend/src/components/Sidebar.jsx`、`frontend/src/components/ContextBar.jsx`
  - 新增 `frontend/src/pages/Tasks.jsx`、`frontend/src/pages/Capabilities.jsx`、`frontend/src/pages/Settings.jsx`
  - 修改 `frontend/src/App.jsx`（工作台嵌套路由）、`frontend/src/pages/Chat.jsx`（适配工作区外壳）、`frontend/src/api/client.js`（新增 deerflow 控制接口）、`frontend/src/styles/global.css`（工作台三栏样式）
  - 新增 `backend/app/services/deerflow_control.py`（DeerFlow 控制代理层）
  - 修改 `backend/app/api/routes.py`（新增 deerflow 控制端点）、`backend/app/schemas/schemas.py`（新增 skill/model/status schema）
  - 新增 `backend/tests/test_deerflow_control.py`

## ADDED Requirements

### Requirement: 工作台三栏外壳
系统 SHALL 提供一个类 Codex 的工作台外壳，包含左侧可折叠导航（对话/任务/能力/设置）、顶部上下文条（学生名、DeerFlow 状态、当前模型）与中间工作区路由出口，并在桌面/平板/移动端响应式适配。

#### Scenario: 桌面进入工作台
- **WHEN** 用户带 `email` 参数进入 `/app/chat`
- **THEN** 显示左侧导航 + 顶部上下文条 + 对话工作区，导航高亮"对话"

#### Scenario: 移动端折叠导航
- **WHEN** 视口宽度小于 768px
- **THEN** 左侧导航收起为可点击展开的抽屉，工作区占满主区域

### Requirement: 任务管理视图
系统 SHALL 在工作台内提供任务管理视图，列出当前学生的全部微行动任务及状态，支持进入打卡页。

#### Scenario: 查看任务列表
- **WHEN** 用户在工作台点击"任务"
- **THEN** 按状态分组展示该学生任务（进行中/已完成/已过期），空态给出去对话生成任务的引导

#### Scenario: 从任务进入打卡
- **WHEN** 用户点击某个进行中的任务
- **THEN** 跳转到该任务的打卡页 `/checkin?task_id=<id>`

### Requirement: 能力控制视图
系统 SHALL 在工作台内提供能力控制视图，展示 DeerFlow 已加载的 skills 与可用模型，并支持开关单个 skill。

#### Scenario: 展示能力清单
- **WHEN** 用户打开"能力"视图且 DeerFlow 可达
- **THEN** 列出 skills（名称/描述/启用态）与模型列表，标注当前对话引擎与模型

#### Scenario: 开关 skill
- **WHEN** 用户切换某个 skill 的启用开关
- **THEN** 前端调用 Awaken 代理接口，代理转发 DeerFlow `PUT /api/skills/{name}`，成功后开关状态更新

#### Scenario: DeerFlow 不可达降级
- **WHEN** DeerFlow gateway 不可达
- **THEN** 能力视图显示"对话引擎离线"提示与重试入口，不抛未捕获异常、不白屏

### Requirement: DeerFlow 控制代理
系统 SHALL 在 Awaken 后端提供一组代理接口，转发 DeerFlow 的 skills/models/status 查询与 skill 开关，统一处理鉴权与不可达降级（返回明确的 online=false 状态而非 500）。

#### Scenario: 查询状态
- **WHEN** 前端请求 `GET /api/deerflow/status`
- **THEN** 返回 `{online: bool, model: str|null, assistant_id: str}`；DeerFlow 不可达时 `online=false` 且 HTTP 200

#### Scenario: 代理 skill 列表
- **WHEN** 前端请求 `GET /api/deerflow/skills`
- **THEN** 返回 DeerFlow skills 列表；不可达时返回空列表与 online=false，不抛 500

## MODIFIED Requirements

### Requirement: 对话视图
对话功能 SHALL 保留现有全部能力（多轮苏格拉底对话、3 轮后阶段切换、接受任务写回后端），但改为嵌入工作台工作区内呈现，复用顶部上下文条，移除页内独立 Navbar。

#### Scenario: 工作台内对话
- **WHEN** 用户在 `/app/chat?email=xxx` 发送消息
- **THEN** 行为与原 `/chat` 一致（气泡、加载态、阶段切换、接受任务跳打卡），但布局位于工作区中

## REMOVED Requirements

### Requirement: 独立整页 /chat 的 Navbar 承载
**Reason**: 工作台由左侧边栏承载导航，页内营销/App Navbar 在工作台内冗余。
**Migration**: 保留 `/chat` 旧路由重定向到 `/app/chat` 以兼容邮件历史链接；营销页 `Navbar` 组件本身不动。
