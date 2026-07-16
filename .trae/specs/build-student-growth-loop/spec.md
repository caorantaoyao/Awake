# 学生端成长闭环 Spec

## Why

当前学生端已具备注册登录、对话、任务生成与打卡的基础链路，但仍缺少 PRD 定义的持续理解、今日行动、资源连接和成长可视化。现有业务接口还允许按任意邮箱读写数据，继续扩展画像会放大未成年人数据暴露风险，因此必须先建立登录学生的数据归属边界。

## What Changes

- 将学生业务接口统一约束为当前登录学生，仅保留健康检查、注册和登录为公开接口。
- 持久化学生成长画像、对话记录、微行动属性和成长事件，形成可追踪的数据闭环。
- 新增学生首页，聚合今日任务、画像摘要、推荐资源和最近成长。
- 将任务升级为 Today's Mission，支持预计时长、成长值、专注计时与完成反馈。
- 新增 Explore 资源页，使用可解释的标签匹配推荐课程、活动、竞赛和实践。
- 新增 Growth 页面，展示动态画像、成长时间线和基于真实任务数据生成的周摘要。
- 在 DeerFlow 独立仓库的 `skills/custom/` 下新增 Awaken 学生成长 Skill，仅以 Skill 形式约束画像提炼、任务生成和资源建议，不修改 DeerFlow 基座后端。
- 保留 DeerFlow 不可达时的 mock 降级，学生主链路不得因外部 Agent 服务失败而白屏或返回 500。
- 不实现老师端、家长端、学校端、复杂推荐算法、外部真实资源抓取和实时状态感知。

## Impact

- Affected specs: 学生鉴权、动态成长画像、Today's Mission、AI Focus、Explore、Growth Map、DeerFlow Skill
- Affected code:
  - `backend/app/models/models.py`
  - `backend/app/schemas/schemas.py`
  - `backend/app/core/migrations.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/deerflow_service.py`
  - `backend/tests/`
  - `frontend/src/App.jsx`
  - `frontend/src/api/client.js`
  - `frontend/src/layouts/WorkspaceLayout.jsx`
  - `frontend/src/components/`
  - `frontend/src/pages/`
  - `frontend/src/styles/global.css`
  - `deer-flow/skills/custom/awaken-student-growth/SKILL.md`

## ADDED Requirements

### Requirement: 登录学生数据边界

系统 SHALL 使用 Bearer JWT 识别当前学生，所有学生画像、对话、任务、成长记录和推荐接口 SHALL 仅操作该学生自己的数据。

#### Scenario: 已登录学生读取自己的成长数据

- **WHEN** 学生携带有效 Token 请求学生业务接口
- **THEN** 系统返回 Token 所属学生的数据，且不需要客户端提交邮箱作为身份依据

#### Scenario: 未登录请求业务数据

- **WHEN** 请求未携带有效 Token
- **THEN** 系统返回 401，不返回任何学生数据

#### Scenario: 尝试访问他人任务

- **WHEN** 已登录学生请求不属于自己的任务 ID
- **THEN** 系统返回 404，且不泄露该任务是否存在

### Requirement: 动态成长画像

系统 SHALL 为每个学生保存一个可持续更新的成长画像，至少包含兴趣标签、能力标签、探索阶段、画像摘要和更新时间。

#### Scenario: 首次进入成长首页

- **WHEN** 学生尚无画像
- **THEN** 系统返回结构稳定的空画像，并引导学生通过对话开始探索

#### Scenario: 对话形成新画像

- **WHEN** 学生完成至少三轮有效探索并生成微行动
- **THEN** 系统基于对话结果更新该学生画像，同时保留更新时间

#### Scenario: Agent 不可达

- **WHEN** DeerFlow 不可达或输出无法解析
- **THEN** 系统使用确定性的本地提炼逻辑更新最小画像，主请求不返回 500

### Requirement: 对话记忆

系统 SHALL 持久化当前学生的用户与助手消息，并按时间顺序返回最近对话，使学生刷新页面后可以继续探索。

#### Scenario: 刷新对话页

- **WHEN** 学生已有历史消息并重新打开对话页
- **THEN** 页面恢复最近消息，不重复创建欢迎消息

#### Scenario: 消息写入失败

- **WHEN** Agent 已回复但消息持久化失败
- **THEN** 接口返回明确错误且不伪造成功写入状态

### Requirement: Today's Mission

系统 SHALL 将微行动表示为包含描述、预计时长、成长值、状态、截止时间和完成反馈的任务，并在学生首页突出一个当前最优先任务。

#### Scenario: 生成今日任务

- **WHEN** 学生完成探索并接受任务
- **THEN** 系统创建一条属于该学生的进行中任务，预计时长范围为 5-30 分钟，成长值为正整数

#### Scenario: 多个进行中任务

- **WHEN** 学生存在多个进行中任务
- **THEN** 首页按截止时间和创建时间选择一个主任务，其余任务仍可在微行动页查看

#### Scenario: 完成任务

- **WHEN** 学生提交可选反馈并完成任务
- **THEN** 系统幂等地记录完成时间、成长值和成长事件，重复提交不会重复累计

### Requirement: AI Focus

系统 SHALL 提供本地可恢复的专注计时体验，支持开始、暂停、继续和结束，并以任务预计时长为默认值。

#### Scenario: 开始专注

- **WHEN** 学生从今日任务启动专注
- **THEN** 页面显示剩余时间、任务内容和暂停/结束控制

#### Scenario: 刷新页面

- **WHEN** 专注计时进行中且学生刷新页面
- **THEN** 页面根据持久化的开始时间和暂停状态恢复合理剩余时间

#### Scenario: 减少动态效果

- **WHEN** 系统启用 `prefers-reduced-motion`
- **THEN** 专注页不使用循环缩放或位移动画，功能保持完整

### Requirement: Explore 资源推荐

系统 SHALL 提供一组受控的示例成长资源，并基于学生兴趣、能力、阶段和最近任务使用可解释规则排序。

#### Scenario: 有画像的学生浏览资源

- **WHEN** 学生打开 Explore
- **THEN** 系统返回按匹配度排序的资源，并为每项给出简短推荐理由

#### Scenario: 无画像的学生浏览资源

- **WHEN** 学生尚无有效标签
- **THEN** 系统返回适合其年级和探索阶段的通用资源，不显示虚假的个性化断言

#### Scenario: 资源类型筛选

- **WHEN** 学生选择课程、活动、竞赛或实践类型
- **THEN** 页面仅展示对应类型，并保留加载、空态和错误态

### Requirement: Growth Map

系统 SHALL 从真实任务创建、任务完成和画像更新事件生成成长时间线，并提供最近七天的行动摘要。

#### Scenario: 查看成长时间线

- **WHEN** 学生打开 Growth 页面
- **THEN** 页面按时间倒序展示真实成长事件，不生成不存在的经历

#### Scenario: 查看七天摘要

- **WHEN** 最近七天存在任务记录
- **THEN** 系统返回创建数、完成数、累计成长值和最活跃兴趣方向

#### Scenario: 无成长记录

- **WHEN** 学生尚未完成任何探索或任务
- **THEN** 页面展示明确空态并提供回到对话的唯一主动作

### Requirement: 学生工作台视觉系统

系统 SHALL 使用现有 React/Vite 和手写 CSS 实现一致的学生端工作台，不新增 UI、状态管理或动画依赖。

设计读取：学生成长产品工作台，采用“学习手账 + 精密工具台”的克制编辑风格，冷白与墨蓝为基底，单一湖蓝强调色；变化度 6、动效 4、信息密度 6。

#### Scenario: 桌面端

- **WHEN** 视口为 1366×768
- **THEN** 首页、对话、微行动、Explore 和 Growth 无横向滚动，主要动作在首屏可见

#### Scenario: 移动端

- **WHEN** 视口为 390×844 或 320×568
- **THEN** 多栏布局明确折叠为单栏，触控目标不小于 44×44px，底部输入与安全区不冲突

#### Scenario: 完整 UI 状态

- **WHEN** 数据处于加载、空、错误、降级或成功状态
- **THEN** 每种状态互斥且可理解，错误态提供恢复动作，DeerFlow 降级不使用阻断性错误视觉

### Requirement: DeerFlow 学生成长 Skill

系统 SHALL 通过单个自包含 Skill 扩展 DeerFlow 的学生成长能力，不修改 DeerFlow Gateway、Harness、模型路由或持久化代码。

#### Scenario: Skill 被 Agent 使用

- **WHEN** 小海需要提炼画像、生成微行动或给出资源建议
- **THEN** Skill 提供中文输出规则、教育伦理边界和机器可解析的 JSON 契约

#### Scenario: Skill 输出职业建议

- **WHEN** 信息不足或涉及学生未来选择
- **THEN** Skill 明确使用建议性语言，不替学生做决定，不编造院校、就业或资源事实

## MODIFIED Requirements

### Requirement: 对话接口

`POST /api/chat` SHALL 要求登录，将消息写入当前学生对话记录，调用 DeerFlow 或 mock 后写入助手回复，并返回是否可生成任务。客户端不再通过 `student_name` 或 email 决定身份。

### Requirement: 任务接口

任务创建、查询、完成和对话提炼任务接口 SHALL 依据当前登录学生确定归属；旧 email 请求字段可以在过渡期被 schema 接受，但 SHALL 被忽略并在测试中验证不可越权。

### Requirement: 工作台导航

学生一级导航 SHALL 调整为“今日、对话、微行动、探索、成长”；账号设置作为底部工具入口。DeerFlow Capabilities 不属于学生导航，普通学生直接访问 SHALL 被重定向。

## REMOVED Requirements

### Requirement: 邮箱作为业务接口身份

**Reason**: email 是可猜测标识，不能作为未成年人业务数据的授权依据。

**Migration**: 前端统一使用现有 Token；兼容邮件链接仅用于跳转登录或恢复当前账号，不再授权读取 query email 对应的数据。

### Requirement: 学生端 Skill 控制面板

**Reason**: Skill 开关和模型信息属于内部运维能力，与学生成长目标无关，并存在越权操作风险。

**Migration**: 保留内部代码供开发联调，但从学生导航移除，普通学生路由不可访问。
