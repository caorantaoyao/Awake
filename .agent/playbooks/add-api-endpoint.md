# Playbook: Add an API Endpoint

新增 HTTP 接口。

## When To Use
- 产品要求新的读/写能力（如"获取学生历史任务列表"、"删除任务"、"学生修改年级"）
- 为前端新页面提供数据
- 拆分现有过大的路由处理函数

## Decision Checklist
- [ ] 接口是读（GET）还是写（POST/PUT/DELETE）？是否改变状态？
- [ ] 是否需要 DB 写入？→ 需要 `db: Session = Depends(get_db)` + `try/except + rollback`
- [ ] 是否调用 DeerFlow 或外部服务？→ 必须 mock 降级
- [ ] 身份如何标识？（当前 MVP 仅 email，无 Token；不要假设鉴权已存在）
- [ ] 幂等性？POST 写接口重复调用是否安全？参考 `/api/task-complete` 的幂等模式
- [ ] 响应包装：统一用 `ApiResponse`（列表/单实体查询例外，保持项目现有风格）

## Implementation Path
| Step | Module | Files | Change |
| --- | --- | --- | --- |
| 1 | Schema | [schemas.py](file:///Users/bytedance/Awake/backend/app/schemas/schemas.py) | 定义 Request/Response Pydantic 模型；字段用 `Field(...)` 加约束 |
| 2 | Route | [routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py) | 加 `@router.get/post(...)` 装饰器；参数正确；返回 Pydantic 或 ApiResponse |
| 3 | Service (optional) | `backend/app/services/*.py` | 如果业务复杂（含外部调用、解析逻辑），抽到 service 保持 route 薄 |
| 4 | Client | [client.js](file:///Users/bytedance/Awake/frontend/src/api/client.js) | 导出新函数；chat/extract-task 类慢接口必须把 timeout 设为 130000 |
| 5 | Frontend | `frontend/src/pages/*.jsx` | 新页面需在 [App.jsx](file:///Users/bytedance/Awake/frontend/src/App.jsx) 加 Route，Navbar variant 正确 |
| 6 | Tests | [test_api.py](file:///Users/bytedance/Awake/backend/tests/test_api.py) | 至少覆盖：200 成功、404 资源不存在、422 参数非法、（写接口）重复/幂等 |

## Do Not
- 不要在路由函数里手写参数校验：全部交给 Pydantic `Field(min_length=...)`、`EmailStr`。
- 不要把外部服务异常直接抛到前端：外部调用必须 try/except 并降级或返回友好错误码。
- 不要在 GET 请求体里塞 JSON——GET 用 path/query 参数。
- 不要漏掉 `db.rollback()`：所有写路径 except 分支必须回滚。
- 不要忘记把新路由通过 `app.include_router(router)` 注册——当前只有一个 router（[routes.py](file:///Users/bytedance/Awake/backend/app/api/routes.py)），在文件末尾加装饰器即可。

## Verification
- Unit: `cd backend && pytest -v tests/test_api.py -k "<your_endpoint_keyword>"`
- Schema check: 启动后端访问 `http://localhost:8000/docs`，看新接口是否在 OpenAPI 里正确出现
- Manual: 用 curl/前端触发一次成功 + 一次失败路径
- Frontend build: `cd frontend && npm run build`（如果改了 client.js 或页面）
- 兼容性：
  - 是否新增了非可选字段但没给默认值？→ 旧请求会 422
  - 是否改变了已有响应结构？→ 前端消费处必须同步
