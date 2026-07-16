# Playbook: Change Chat Behavior（小海对话行为）

修改「小海」人设、对话阶段规则、回复风格、工具调用策略或提炼任务逻辑。

## When To Use
- 调整小海人设、语气、自我介绍
- 修改"探索期/解锁期"轮次阈值、规则内容
- 改 DeerFlow 调用参数（assistant_id、超时、thread 策略、返回解析）
- 改 mock 降级脚本文案
- 调整"可提炼任务"出现时机/卡片文案
- 改提炼任务的 prompt 或长度限制

## Decision Checklist
- [ ] 改动是 prompt 层还是编排层？prompt → 只动 config.py；编排 → deerflow_service.py
- [ ] 是否涉及 DeerFlow skill 可见性/开关？→ 学生端无权操作控制接口；仅在内部联调环境使用保留的 Capabilities 代码
- [ ] 轮次阈值改了吗？→ `XIAOHAI_UNLOCK_AFTER_TURNS` 必须与 [routes.py:284-285](file:///Users/bytedance/Awake/backend/app/api/routes.py#L284-L285) 的 `can_extract_task` 判断同步
- [ ] 改后是否还能在 DeerFlow 挂掉时安全降级到 mock？→ 必须保持
- [ ] 提炼任务的 prompt 是否会导致返回超长？前端卡片/任务描述列是 Text，能容纳，但飞书卡片显示体验需评估
- [ ] 前端超时够吗？改慢回答后需同步前端(130s) / Vite proxy(130s) / nginx(130s) / 后端 httpx(120s) 四处超时

## Implementation Path
| Step | Module | Files | Change |
| --- | --- | --- | --- |
| 1 | Prompt 常量 | [config.py:37-58](file:///Users/bytedance/Awake/backend/app/core/config.py#L37-L58) | 改 `XIAOHAI_PERSONA_PROMPT` / `XIAOHAI_EXPLORE_PROMPT` / `XIAOHAI_UNLOCK_PROMPT` / `XIAOHAI_UNLOCK_AFTER_TURNS` |
| 2 | Threshold sync | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | 若改了阈值，同步修改 `can_extract_task` 的轮次判断 |
| 3 | Orchestration (optional) | [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | `_build_system_prompt`、`_run_deerflow`、`_extract_last_ai_text`、`chat`、`extract_task`、`_mock_*` 按需修改 |
| 4 | Mock script | [deerflow_service.py](file:///Users/bytedance/Awake/backend/app/services/deerflow_service.py) | `_mock_socratic_reply` 与 `_mock_extract_task` 的脚本/关键词需同步调整语气或领域 |
| 5 | Frontend (optional) | [Chat.jsx](file:///Users/bytedance/Awake/frontend/src/pages/Chat.jsx) | 打字态文案、提取卡片文案、欢迎语 fallback |
| 6 | Tests | [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) (TestChatAPI/TestExtractTaskAPI) | 调整轮次阈值相关断言；补新分支用例（注意测试默认 DeerFlow=mock，不会真调 LLM） |

## 关键不变量（破坏即回归）
- `_build_system_prompt` 必须保证探索期与解锁期 prompt **互斥二选一**，不能同时拼接两段规则——会让 DeepSeek 在"只提问"和"给建议"之间反复横跳。
- `_run_deerflow` 的异常必须向上抛给 `chat()`/`extract_task()` 的 except 做 mock 降级，不要在底层吞异常。
- `_extract_last_ai_text` 必须跳过空 content 的 AI 消息（工具调用占位）。
- thread_id 使用 uuid 每次新建（无状态），全量历史由前端 messages 携带。若改成长连接 thread 复用，必须引入会话存储与历史裁剪，否则记忆会在进程重启/多实例间漂移。
- 超时链路：前端 axios(chat 130s) ≥ Vite proxy(130s) ≥ nginx proxy_read_timeout(130s) ≥ 后端 httpx(120s)；DeerFlow 控制接口独立 60s。

## Do Not
- 不要在本仓库修改 DeerFlow 加载哪些 skill/模型——那是 deer-flow 侧 config.yaml 的事；本仓库只能通过控制面板在运行时开关已加载的 skill。
- 不要把小海人设写到前端 JSX 里——单一事实源是后端 config.py（方便 A/B 与热改）。
- 不要让 `extract_task` 返回带引号/前缀/解释的文字——飞书卡片与任务列表直接展示 description，要求纯文本。
- 不要删除 mock 脚本——它是 DeerFlow 不可用时的核心兜底，也是测试环境唯一路径。
- 不要假设 DeerFlow 是 OpenAI 兼容——对话必须走 LangGraph `POST /api/runs/wait`。

## Verification
- Unit: `cd backend && pytest -v tests/test_api.py::TestChatAPI tests/test_api.py::TestExtractTaskAPI`
  - 特别关注 `test_chat_can_extract_after_three_turns`：若改了阈值 N，必须把测试里的 user 消息数调到 N
- Integration (local):
  1. 启动 DeerFlow（`DEER_FLOW_AUTH_DISABLED=1`）
  2. 启动 backend
  3. 登录后在前端 `/app/chat` 连续发 ≥N+1 轮，验证：
     - 前 N-1 轮小海主要在追问，不给结论
     - 第 N 轮起出现"接受今天的微行动任务"卡片
     - 点击后能生成任务并跳 `/app/focus?task_id=...`
- 降级验证：停掉 DeerFlow，再发消息→应返回 mock 文案，接口 200，不抛错；后端日志有 "降级到 mock" 字样
- 前端：长回复（>30s）不会被代理或 axios 超时截断
- 样式：AI 回复多段换行正确渲染（`white-space: pre-wrap`）
