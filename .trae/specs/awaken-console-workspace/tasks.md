# Tasks

- [x] Task 1: DeerFlow 控制代理层（后端）：新增 `backend/app/services/deerflow_control.py`，封装对本地 DeerFlow gateway 的 skills/models/status 查询与 skill 开关，统一鉴权头与不可达降级（绝不抛 500）。
  - [x] SubTask 1.1: `get_status()` → 探测 DeerFlow 是否在线、返回当前 assistant_id 与模型名
  - [x] SubTask 1.2: `list_skills()` / `set_skill_enabled(name, enabled)` → 转发 GET `/api/skills`、PUT `/api/skills/{name}`
  - [x] SubTask 1.3: `list_models()` → 转发 GET `/api/models`
  - [x] SubTask 1.4: 所有方法在连接失败时返回结构化降级值（online=false / 空列表），不抛异常

- [x] Task 2: 后端控制端点 + schema：在 `backend/app/api/routes.py` 新增 `/api/deerflow/status`、`/api/deerflow/skills`(GET)、`/api/deerflow/skills/{name}`(PUT)、`/api/deerflow/models`(GET)；在 `schemas.py` 新增对应响应模型。
  - [x] SubTask 2.1: schema：`DeerFlowStatusResponse`、`SkillItem`/`SkillListResponse`、`ModelItem`/`ModelListResponse`、`SkillToggleRequest`
  - [x] SubTask 2.2: 路由接线并挂到现有 router

- [x] Task 3: 前端 API 客户端：在 `frontend/src/api/client.js` 新增 `getDeerflowStatus/getSkills/toggleSkill/getModels`。

- [x] Task 4: 工作台三栏外壳（前端）：新增 `layouts/WorkspaceLayout.jsx` + `components/Sidebar.jsx` + `components/ContextBar.jsx`，实现左侧可折叠导航、顶部上下文条、中间 `<Outlet/>`，并在 `App.jsx` 建立 `/app/*` 嵌套路由；`/chat` 重定向到 `/app/chat`。视觉需精致、有品牌一致性、响应式（桌面/平板/移动）。
  - [x] SubTask 4.1: Sidebar（对话/任务/能力/设置 + 折叠）
  - [x] SubTask 4.2: ContextBar（学生名 + DeerFlow 在线状态点 + 当前模型）
  - [x] SubTask 4.3: App.jsx 嵌套路由与 `/chat`→`/app/chat` 重定向
  - [x] SubTask 4.4: global.css 三栏工作台样式（含移动端抽屉）

- [x] Task 5: 对话视图适配：将 `pages/Chat.jsx` 改为工作区内视图（移除页内 Navbar，复用 ContextBar），保留多轮/阶段切换/接受任务全部现有逻辑不回退。

- [x] Task 6: 任务管理视图：新增 `pages/Tasks.jsx`，用 `getStudent(email)` 拉取任务，按状态分组展示，进行中任务可跳 `/checkin?task_id=`，含空态引导。

- [x] Task 7: 能力控制视图：新增 `pages/Capabilities.jsx`，展示 skills（可开关）与模型列表，DeerFlow 离线时显示降级提示与重试。

- [x] Task 8: 设置/关于视图：新增 `pages/Settings.jsx`，只读展示 DeerFlow 状态、模型、阶段阈值、健康检查。

- [x] Task 9: 后端测试：`backend/tests/test_deerflow_control.py`，覆盖 status/skills/models 在 DeerFlow 不可达时的降级（online=false、不 500）。

- [x] Task 10: 联调与验证：启动 DeerFlow(8001)+Awaken(8000)+前端(3000)，浏览器验证工作台四视图可用、对话闭环不回退、能力开关生效、离线降级；后端 pytest 全过、前端 build 通过。

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 无前置（外壳可先搭）
- Task 5 depends on Task 4
- Task 6 depends on Task 4
- Task 7 depends on Task 3, Task 4
- Task 8 depends on Task 3, Task 4
- Task 9 depends on Task 1, Task 2
- Task 10 depends on Task 5, Task 6, Task 7, Task 8, Task 9
- 可并行：Task 1（后端链）与 Task 4（前端外壳）可同时起；Task 5/6 可并行；Task 7/8 可并行
