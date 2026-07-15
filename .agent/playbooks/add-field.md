# Playbook: Add / Change a Field

给 Student 或 Task 加/改字段。

## When To Use
- 产品要求在学生信息或任务卡片上显示新字段（如学生"性别""学校"，任务"分类""预计时长"）
- 需要把已有字段改名/改类型/改长度
- 需要让新字段出现在注册表单、打卡页、邮件、飞书通知中

## Decision Checklist
- [ ] 字段是 Student 还是 Task 的属性？不要混放
- [ ] 该字段是否需要用户输入？→ 需要改前端表单；仅后端生成 → 不用
- [ ] 是否影响邮件/飞书卡片？→ 改对应 service 模板
- [ ] 是否需要枚举值？→ 复用现有 `GradeEnum`/`TaskStatusEnum` 的 str-enum 模式
- [ ] 本地开发可接受删库重建？（当前无迁移框架）；生产部署 `Needs verification`（需先引入 Alembic）

## Implementation Path
| Step | Module | Files | Change |
| --- | --- | --- | --- |
| 1 | ORM | [models.py](file:///Users/bytedance/Awake/backend/app/models/models.py) | 新增/修改 Column；非空字段给 server_default 或 nullable=True |
| 2 | Schema | [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) | Request 加 Field 校验；Response 加字段；注意 `from_attributes = True` |
| 3 | Route | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | 创建/更新时读取并赋值；返回时通过 Pydantic 自动带出 |
| 4 | API client | [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) | 无需改（直接返回 JSON），除非调用侧有类型约束 |
| 5 | Frontend page | `frontend/src/pages/*.jsx` | 表单加输入；展示加渲染；注意 Navbar variant |
| 6 | Notifications (optional) | [email_service.py](file:///Users/bytedance/Awake/backend/app/services/email_service.py), [feishu_service.py](file:///Users/bytedance/Awake/backend/app/services/feishu_service.py) | 模板中嵌入新字段（HTML 注意转义） |
| 7 | Tests | [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) | 覆盖成功/非法值/缺省场景；断言新字段返回值 |
| 8 | DB | 本地 `backend/awaken.db` | 停服 → 删文件 → 重启；或手动 `ALTER TABLE ADD COLUMN` |

## Do Not
- 不要直接上生产环境跑 `create_all()` 期望自动迁移——SQLAlchemy 不会 ALTER 已有列。
- 不要在 routes 里用 `setattr` 批量设置未声明字段，必须显式列出新字段名。
- 不要把非 ASCII/特殊字符的枚举值硬改成 int；现有枚举存中文显示值。
- 不要让新字段破坏现有测试：测试依赖的 `_register_student` 等辅助函数需同步补齐必填字段。

## Verification
- Unit: `cd backend && pytest -v`（必须全绿；新加字段必须加测试）
- Integration: 本地跑三进程（见 AGENTS.md），走注册→对话→提炼任务→打卡完整链路
- Data: 用 `sqlite3 backend/awaken.db ".schema students"` / `.schema tasks` 确认列存在
- Manual: 前端对应页面新增/编辑/展示符合预期
- 兼容性检查：
  - 旧前端调用是否因缺字段 422？→ Request 新字段给默认值或 `Optional`
  - 旧 DB 行新列为 NULL 是否会 500？→ Response 字段 `Optional` 或给 default
