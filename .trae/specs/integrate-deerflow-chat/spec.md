# 集成 DeerFlow 作为本地对话引擎（替换飞书 Aily）Spec

## Why
当前 Awaken MVP 的 AI 苏格拉底对话原本依赖飞书 Aily 智能伙伴，但飞书多维表格「接收 Webhook」是付费增值功能，且 Aily 入口只能在飞书客户端打开，无法闭环验证。改用开源 DeerFlow 作为本地对话引擎，可让前端直接与本地 AI 对话，完成「苏格拉底引导 → 生成微任务 → 写回后端」的完整闭环，零外部付费依赖。

## What Changes
- **BREAKING**：移除飞书 Aily 作为对话入口，改为前端内置聊天页面对接本地 DeerFlow。
- 新增后端「对话代理层」(`deerflow_service`)，作为 Awaken 后端与本地 DeerFlow 服务之间的 HTTP 适配器，隔离 DeerFlow API 契约的不确定性。
- 新增后端对话接口：`POST /api/chat`（转发到 DeerFlow，支持流式）与 `POST /api/chat/extract-task`（从对话中提炼微任务并写回任务表）。
- 新增前端聊天页面 `/chat`，实现与「小海」的多轮苏格拉底对话，对话结束后一键「接受任务」写回后端。
- 邮件欢迎链接从 Aily 链接改为指向前端 `/chat` 页面。
- DeerFlow 以**独立本地服务**方式运行（独立 clone、独立 venv/Docker、独立端口），不并入 Awaken 后端 venv，避免 langchain 版本冲突。
- 「小海」苏格拉底人设通过 system prompt 注入 DeerFlow 请求，而非依赖 DeerFlow 内置技能。

## Impact
- Affected specs: AI 对话能力、任务生成链路、注册邮件跳转
- Affected code:
  - `backend/app/services/deerflow_service.py`（新增）
  - `backend/app/services/email_service.py`（欢迎链接改向）
  - `backend/app/api/routes.py`（新增 chat 接口）
  - `backend/app/schemas/schemas.py`（新增 chat 相关 schema）
  - `backend/app/core/config.py`（新增 DeerFlow 配置项）
  - `backend/.env.example`（新增 DeerFlow 配置）
  - `frontend/src/pages/Chat.jsx`（新增）
  - `frontend/src/api/client.js`（新增 chat 方法）
  - `frontend/src/App.jsx`（新增 /chat 路由）
  - `frontend/src/pages/Success.jsx`（引导改向 /chat）
  - `backend/tests/test_api.py`（新增 chat 接口测试，DeerFlow 走 mock）

## ADDED Requirements

### Requirement: DeerFlow 对话代理层
系统 SHALL 提供一个后端服务模块，将前端对话请求转发到本地运行的 DeerFlow 服务，并注入「小海」苏格拉底 system prompt。当 DeerFlow 未启用或不可达时，SHALL 降级到内置 mock 苏格拉底对话逻辑，保证前端闭环可演示。

#### Scenario: DeerFlow 可达时正常转发
- **WHEN** 前端向 `/api/chat` 发送用户消息且 `DEERFLOW_ENABLED=true`
- **THEN** 后端将消息（含 system prompt 与历史）转发到 DeerFlow，返回 AI 回复

#### Scenario: DeerFlow 不可达时降级
- **WHEN** `DEERFLOW_ENABLED=false` 或 DeerFlow 连接失败
- **THEN** 后端返回内置 mock 苏格拉底式回复，且响应中标记 `mode=mock`，不抛 500

### Requirement: 苏格拉底对话与微任务生成
系统 SHALL 在对话进行 3 轮以上后，支持从对话上下文中提炼出一个符合 SMART 原则的微行动任务，并写回该学生的任务表。

#### Scenario: 从对话提炼任务
- **WHEN** 前端调用 `/api/chat/extract-task` 并携带学生邮箱与对话历史
- **THEN** 后端生成一条微任务描述并在任务表创建记录，返回 task 对象

#### Scenario: 未注册学生提炼任务
- **WHEN** 携带的邮箱在学生表中不存在
- **THEN** 返回 404，提示学生不存在

### Requirement: 前端聊天界面
系统 SHALL 提供一个与 Awaken 品牌一致、精美且响应式的聊天页面，支持多轮对话、加载态、消息流展示、以及对话后「接受任务」入口。

#### Scenario: 用户进行多轮对话
- **WHEN** 用户在 `/chat?email=xxx` 输入消息并发送
- **THEN** 界面展示用户气泡与「小海」回复气泡，输入框在请求期间禁用并显示加载态

#### Scenario: 接受生成的任务
- **WHEN** 对话达到可生成任务条件，用户点击「接受任务」
- **THEN** 调用 extract-task 接口，成功后跳转到打卡页 `/checkin?task_id=xxx`

## MODIFIED Requirements

### Requirement: 注册欢迎邮件
注册成功后系统 SHALL 发送欢迎邮件，邮件中的行动按钮 SHALL 指向前端 `/chat` 页面（携带学生邮箱参数），而非飞书 Aily 链接。

#### Scenario: 邮件跳转到本地对话
- **WHEN** 学生点击欢迎邮件中的「开始与小海对话」按钮
- **THEN** 浏览器打开 `FRONTEND_URL/chat?email=<学生邮箱>`

## REMOVED Requirements

### Requirement: 飞书 Aily 对话入口
**Reason**: 飞书 Aily 需付费增值功能且无法在浏览器闭环，改用本地 DeerFlow。
**Migration**: 邮件链接改指向前端 `/chat`；`feishu_service` 保留但不再作为对话入口（其 webhook 通知能力保持 mock 模式，不在本次改动范围）。
