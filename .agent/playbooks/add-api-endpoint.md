# Playbook: Add an API Endpoint

新增 HTTP 接口。

## When To Use
- 产品要求新的读/写能力（如"获取学生历史任务列表"、"删除任务"、"学生修改年级"）
- 为前端新页面提供数据（Workspace 内页或顶层页面）
- 拆分现有过大的路由处理函数
- 新增 DeerFlow 控制面板代理接口

## Decision Checklist
- [ ] 接口是读（GET）还是写（POST/PUT/DELETE）？是否改变状态？
- [ ] 是否需要 DB 写入？→ 需要 `db: Session = Depends(get_db)` + `try/except + rollback`
- [ ] 是否调用 DeerFlow 或外部服务？
  - 对话类接口：走 deerflow_service，必须 mock 降级（不抛 500）
  - 控制类接口：走 deerflow_control，必须返回 online=false 降级（不抛 500）
  - 通知类接口：best-effort，失败只记日志不抛
- [ ] 是否需要鉴权？→ 新接口默认加 `Depends(get_current_student)`；产品明确要求匿名访问才不加
- [ ] 幂等性？POST 写接口重复调用是否安全？参考 `/api/task-complete` 的幂等模式
- [ ] 响应包装：统一用 `ApiResponse`（列表/单实体查询例外，保持项目现有风格）
- [ ] 超时：对话类慢接口超时 120s（后端 httpx）/ 130s（前端）；控制类接口超时 60s
- [ ] 前端是 Workspace 内页（/app/*）还是顶层页面？→ 影响前端路由和布局选择

## Implementation Path
| Step | Module | Files | Change |
| --- | --- | --- | --- |
| 1 | Schema | [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) | 定义 Request/Response Pydantic 模型；字段用 `Field(...)` 加约束；DeerFlow 相关响应用 `model_config = ConfigDict(extra="allow")` |
| 2 | Service (optional) | `backend/app/services/*.py` | 如果业务复杂（含外部调用、解析逻辑、归一化），抽到 service 保持 route 薄；对话走 deerflow_service，控制走 deerflow_control |
| 3 | Route | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | 加 `@router.get/post/put(...)` 装饰器；参数正确；写路径包 try/except+rollback；外部调用包 try/except+降级；返回 Pydantic 或 ApiResponse |
| 4 | Client | [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) | 导出新函数；chat/extract-task 类慢接口 timeout 设为 130000；DeerFlow 控制接口 timeout 用 controlTimeoutMs（默认 60000） |
| 5 | Frontend | `frontend/src/pages/*.jsx` | Workspace 内页：建页面组件（用 `useOutletContext()`）→ App.jsx `/app` 下加 Route → Sidebar 加导航 → ContextBar 加 SECTION_TITLES；顶层页面：手动包 `<Navbar variant="app" />`（营销页用默认 variant） |
| 6 | Tests | [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) 或 [test_deerflow_control.py](file:///Users/bytedance/Awake/backend/tests/test_deerflow_control.py) | 至少覆盖：200 成功、404 资源不存在、422 参数非法、（写接口）重复/幂等、（外部调用）降级/离线 |

## Do Not
- 不要在路由函数里手写参数校验：全部交给 Pydantic `Field(min_length=...)`、`EmailStr`。
- 不要把外部服务异常直接抛到前端：外部调用必须 try/except 并降级或返回友好错误码。
- 不要在 GET 请求体里塞 JSON——GET 用 path/query 参数。
- 不要漏掉 `db.rollback()`：所有写路径 except 分支必须回滚。
- 不要忘记把新路由通过 `app.include_router(router)` 注册——当前只有一个 router（[routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py)），在文件末尾加装饰器即可。
- 不要让 DeerFlow 控制接口抛 500——必须 catch 异常返回 `online: false` 降级响应。
- 不要在前端 Workspace 页面手动管理全局 deerflowStatus/student——用 Outlet context 的 `setStudent`/`refreshDeerflowStatus`。
- 不要在前端直接访问 localhost:8001（DeerFlow），所有请求经后端代理。

## Verification
- Unit: `cd backend && pytest -v`（全绿）
- Schema check: 启动后端访问 `http://localhost:8000/docs`，看新接口是否在 OpenAPI 里正确出现
- Manual: 用 curl/前端触发一次成功 + 一次失败路径
- DeerFlow 降级验证：停掉 DeerFlow，调新接口→应返回降级响应（online=false 或 mock），不抛 500
- Frontend build: `cd frontend && npm run build`（如果改了 client.js 或页面）
- 兼容性：
  - 是否新增了非可选字段但没给默认值？→ 旧请求会 422
  - 是否改变了已有响应结构？→ 前端消费处必须同步
  - Workspace 页面是否正确出现在 Sidebar 导航？ContextBar 是否显示正确标题？
