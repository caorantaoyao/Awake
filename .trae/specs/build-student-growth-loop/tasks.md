# Tasks

- [x] Task 1: 以测试先行建立学生数据归属边界：为现有业务接口补充无 Token、无效 Token、跨学生访问和身份字段伪造的失败用例，再将任务、学生、对话和 DeerFlow 控制接口收敛到当前登录学生。
  - [x] SubTask 1.1: 先编写并执行鉴权失败测试，确认测试因现有 IDOR 行为失败
  - [x] SubTask 1.2: 业务查询使用 `current_student.id` 限定归属，越权统一返回 404
  - [x] SubTask 1.3: 对话和任务生成不再信任客户端 email、student_id 或 student_name
  - [x] SubTask 1.4: 普通学生不可访问 DeerFlow skill/model 控制接口
  - [x] SubTask 1.5: 复跑鉴权测试并确认通过

- [x] Task 2: 以测试先行扩展成长数据模型和幂等迁移：新增成长画像、对话消息、资源目录、成长事件模型，并为 Task 增加预计时长、成长值和主题标签。
  - [x] SubTask 2.1: 先编写模型约束和旧 SQLite 升级测试，确认缺少新结构时失败
  - [x] SubTask 2.2: 实现 `StudentProfile`、`ConversationMessage`、`GrowthResource`、`GrowthEvent`
  - [x] SubTask 2.3: 扩展 `Task` 的 `estimated_minutes`、`growth_points`、`topic_tags`
  - [x] SubTask 2.4: 实现可重复执行且不破坏旧数据的 SQLite 迁移
  - [x] SubTask 2.5: 复跑迁移和模型测试并确认通过

- [x] Task 3: 在 DeerFlow 独立仓库中新增 Awaken 学生成长 Skill，不修改基座后端。
  - [x] SubTask 3.1: 在 `deer-flow/skills/custom/awaken-student-growth/SKILL.md` 定义触发场景、苏格拉底对话、画像候选、微行动和资源建议规则
  - [x] SubTask 3.2: 定义可解析 JSON 输出契约与失败时的纯文本降级约束
  - [x] SubTask 3.3: 写明未成年人教育伦理、建议性表达、事实查证和禁止敏感推断
  - [x] SubTask 3.4: 使用 DeerFlow 现有 skill 校验能力验证目录和 frontmatter

- [x] Task 4: 以测试先行实现学生成长聚合 API：画像、对话历史、今日任务、资源推荐和成长时间线均只返回当前学生数据。
  - [x] SubTask 4.1: 先编写空画像、画像更新、对话恢复、今日任务排序、推荐确定性和成长事件隔离测试
  - [x] SubTask 4.2: 新增当前学生画像读取和修正接口
  - [x] SubTask 4.3: 改造聊天接口以持久化用户与助手消息，并提供最近历史读取
  - [x] SubTask 4.4: 新增今日任务接口，并使任务完成幂等写入成长事件
  - [x] SubTask 4.5: 新增受控资源目录与可解释规则排序接口
  - [x] SubTask 4.6: 新增成长时间线和最近七天真实数据摘要接口
  - [x] SubTask 4.7: 复跑新增 API 测试并确认通过

- [x] Task 5: 调整 DeerFlow 适配层以消费学生成长 Skill 约束，同时保持不可达降级。
  - [x] SubTask 5.1: 先编写画像提炼、任务结构化输出、非法输出降级和超时降级测试
  - [x] SubTask 5.2: 在现有 prompt 互斥规则上加入 Skill 的结构化结果约束
  - [x] SubTask 5.3: 解析并校验画像候选、任务时长、成长值和标签
  - [x] SubTask 5.4: 保持 DeerFlow 不可达时确定性 mock，不向上抛 500
  - [x] SubTask 5.5: 复跑 DeerFlow 服务测试并确认通过

- [x] Task 6: 建立前端可测试的数据映射基础和 API 客户端。
  - [x] SubTask 6.1: 使用 Node 内置测试能力先编写今日任务选择、资源筛选、成长事件分组和专注计时恢复测试
  - [x] SubTask 6.2: 在 `client.js` 接入画像、历史消息、今日任务、推荐和成长事件接口
  - [x] SubTask 6.3: 将可复用纯逻辑放入最小 helper 模块，不引入第三方依赖
  - [x] SubTask 6.4: 执行前端单元测试并确认通过

- [x] Task 7: 重构学生工作台导航与“今日”首页，复用现有 Workspace 外壳并保留用户未提交改动。
  - [x] SubTask 7.1: 一级导航调整为今日、对话、微行动、探索、成长，账号入口下沉
  - [x] SubTask 7.2: 新增今日首页，展示当前任务、画像摘要、推荐资源和最近成长
  - [x] SubTask 7.3: 普通学生访问 `/app/capabilities` 时重定向到今日页
  - [x] SubTask 7.4: 实现加载、空、错误和 DeerFlow 降级状态，避免重复页面标题

- [x] Task 8: 完成对话、微行动和 AI Focus 学生体验。
  - [x] SubTask 8.1: 对话页恢复历史消息，保留长等待、取消和失败重试行为
  - [x] SubTask 8.2: 任务生成后更新画像摘要和今日任务，不依赖 query email
  - [x] SubTask 8.3: 微行动页改为进行中优先的纵向结构，已完成和已过期弱化
  - [x] SubTask 8.4: 新增可开始、暂停、继续、结束和刷新恢复的专注计时视图
  - [x] SubTask 8.5: 打卡完成后刷新今日页、任务页和成长时间线状态

- [x] Task 9: 完成 Explore 与 Growth 页面，并执行前端设计预检。
  - [x] SubTask 9.1: Explore 提供资源类型筛选、推荐理由和无画像兜底
  - [x] SubTask 9.2: Growth 展示动态画像、最近七天摘要和真实事件时间线
  - [x] SubTask 9.3: 桌面、平板、移动端布局明确折叠，触控目标不小于 44×44px
  - [x] SubTask 9.4: 完成焦点态、语义标签、减少动态效果和安全区处理
  - [x] SubTask 9.5: 执行 frontend-design 与 design-taste-frontend 预检，确保单一强调色、统一圆角、无模板化三等分卡片和工程术语

- [x] Task 10: 按顺序执行完整验证并修复发现的问题。
  - [x] SubTask 10.1: 运行后端全量 pytest 和前端 Node 单元测试
  - [x] SubTask 10.2: 运行前端生产构建
  - [x] SubTask 10.3: 启动本地服务，使用 curl 完成注册、登录、画像、对话、今日任务、资源、打卡和成长时间线接口测试
  - [x] SubTask 10.4: 使用浏览器和 Computer Use 在 1366×768、390×844 验证完整学生路径与控制台
  - [x] SubTask 10.5: 执行 Ponytail 最终审查，删除无调用代码、重复 helper、无依据兜底和非必要改动

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 与 Task 1、Task 2 可并行
- Task 4 depends on Task 1, Task 2
- Task 5 depends on Task 3, Task 4 的接口契约
- Task 6 depends on Task 4 的接口契约
- Task 7 depends on Task 6
- Task 8 depends on Task 5, Task 6, Task 7
- Task 9 depends on Task 6, Task 7
- Task 8 与 Task 9 可并行
- Task 10 depends on Task 1-9
