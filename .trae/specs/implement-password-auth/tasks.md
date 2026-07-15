# Tasks

- [x] Task 1: 后端密码哈希基础能力：在现有认证服务中加入密码哈希与校验能力，并避免新增不必要依赖。
  - [x] SubTask 1.1: 基于已安装的 `python-jose[cryptography]` 依赖中的 cryptography 能力或 Python 标准库实现安全哈希，不存明文密码。
  - [x] SubTask 1.2: 提供 `hash_password(password)` 与 `verify_password(password, password_hash)`。
  - [x] SubTask 1.3: 为密码哈希和校验增加后端测试。

- [x] Task 2: 数据模型与迁移：为 `Student` 增加 `password_hash` 字段，并提供老用户迁移脚本。
  - [x] SubTask 2.1: 更新 ORM 模型与建表结构。
  - [x] SubTask 2.2: 新增幂等迁移脚本，补充 `password_hash` 列并为旧用户生成可登录密码哈希。
  - [x] SubTask 2.3: 在启动初始化或文档约定中确保本地 SQLite 不因缺列导致接口失败。

- [x] Task 3: 后端注册与登录契约：将注册和登录改为邮箱+密码模式，保留现有响应结构。
  - [x] SubTask 3.1: `StudentRegisterRequest` 增加 `password` 字段并校验长度。
  - [x] SubTask 3.2: `StudentLoginRequest` 增加 `password` 字段。
  - [x] SubTask 3.3: 注册时写入 `password_hash`，API 响应不包含密码或哈希。
  - [x] SubTask 3.4: 登录时验证密码，邮箱不存在与密码错误分别返回明确错误。
  - [x] SubTask 3.5: 更新现有注册/登录单测，覆盖正确密码、错误密码、缺失密码、老用户迁移后登录。

- [x] Task 4: 前端注册/登录表单：补齐密码输入体验并保持视觉质量。
  - [x] SubTask 4.1: 注册页新增密码与确认密码输入，前端校验必填、长度、确认一致。
  - [x] SubTask 4.2: 登录页新增密码输入，调用登录接口时提交邮箱和密码。
  - [x] SubTask 4.3: 密码错误、邮箱不存在、注册校验错误以现有 Toast/inline error 方式清晰展示。
  - [x] SubTask 4.4: 保持 Awaken 品牌一致、响应式可用、焦点态清晰；仅在现有样式不足时最小补充 CSS。

- [x] Task 5: 集成验证与回归：验证注册、登录、会话恢复、旧功能不被破坏。
  - [x] SubTask 5.1: 运行后端 pytest 全量测试。
  - [x] SubTask 5.2: 运行前端 `npm run build`。
  - [x] SubTask 5.3: 用本地服务或 API 请求验证正确 credentials 成功登录、错误密码失败、未知邮箱失败。
  - [x] SubTask 5.4: 确认注册成功页、聊天页、打卡相关既有流程不因密码改造回退。

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 1 and Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 3 and Task 4
- 可并行：Task 1 的测试设计与 Task 2 的迁移脚本设计可并行；Task 4 可在 Task 3 契约确定后独立实现。
