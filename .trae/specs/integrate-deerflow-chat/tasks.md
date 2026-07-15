# Tasks

- [x] Task 1: 后端配置与 schema 扩展：为 DeerFlow 集成添加配置项与请求/响应模型
  - [x] SubTask 1.1: 在 `backend/app/core/config.py` 新增 `DEERFLOW_ENABLED`、`DEERFLOW_BASE_URL`、`DEERFLOW_MODEL`、`DEERFLOW_API_KEY`、`XIAOHAI_SYSTEM_PROMPT` 配置项
  - [x] SubTask 1.2: 在 `backend/.env.example` 补充对应 DeerFlow 配置示例（默认 `DEERFLOW_ENABLED=false`）
  - [x] SubTask 1.3: 在 `backend/app/schemas/schemas.py` 新增 `ChatMessage`、`ChatRequest`、`ChatResponse`、`ExtractTaskRequest` 模型

- [x] Task 2: 后端 DeerFlow 对话代理层：实现转发与 mock 降级
  - [x] SubTask 2.1: 新建 `backend/app/services/deerflow_service.py`，实现 `chat(messages, student_name)` 转发到 DeerFlow，失败/未启用时降级到内置苏格拉底 mock 回复（返回 `mode` 标记）
  - [x] SubTask 2.2: 实现 `extract_task(messages, student_name)` 从对话历史生成一条 SMART 微任务描述（DeerFlow 启用时走模型，否则走规则 mock）

- [x] Task 3: 后端对话接口：暴露 `/api/chat` 与 `/api/chat/extract-task`
  - [x] SubTask 3.1: 在 `backend/app/api/routes.py` 新增 `POST /api/chat`，调用 deerflow_service.chat 并返回回复
  - [x] SubTask 3.2: 新增 `POST /api/chat/extract-task`，校验学生存在→生成任务描述→复用现有 Task 写入逻辑创建任务→返回 task
  - [x] SubTask 3.3: 修改 `backend/app/services/email_service.py`，欢迎邮件按钮链接改为 `FRONTEND_URL/chat?email=<邮箱>`

- [x] Task 4: 前端聊天界面与路由接入
  - [x] SubTask 4.1: 在 `frontend/src/api/client.js` 新增 `sendChat`、`extractTask` 方法
  - [x] SubTask 4.2: 新建 `frontend/src/pages/Chat.jsx`，精美响应式聊天 UI（消息气泡、加载态、苏格拉底引导、达标后「接受任务」按钮）
  - [x] SubTask 4.3: 在 `frontend/src/App.jsx` 注册 `/chat` 路由
  - [x] SubTask 4.4: 修改 `frontend/src/pages/Success.jsx`，主 CTA 引导至 `/chat?email=<邮箱>`

- [x] Task 5: 测试与验证
  - [x] SubTask 5.1: 在 `backend/tests/test_api.py` 新增 `/api/chat`（mock 模式）与 `/api/chat/extract-task`（成功 + 404）测试用例
  - [x] SubTask 5.2: 运行 pytest 全量通过；前端 `npm run build` 通过
  - [x] SubTask 5.3: 启动前后端，用内置浏览器走通「注册→进入 /chat→多轮对话→接受任务→打卡」端到端流程并截图验证

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3 (前端依赖后端接口契约)
- Task 5 depends on Task 3 and Task 4
