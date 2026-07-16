# Awaken 前端界面设计审计与问题报告

## 1. 文档目的

本文档用于沉淀 Awaken 当前前端界面的设计审计结果，目标不是做泛泛的“美化建议”，而是明确指出影响用户信任、注册转化、对话完成率和长期产品一致性的具体问题，并给出可执行的修复方向。

当前产品的核心体验是：

1. 用户从 Landing 了解产品价值。
2. 用户注册并进入小海对话。
3. 小海通过多轮对话帮助学生探索方向。
4. 对话沉淀为今天能完成的微行动任务。
5. 用户完成打卡，形成成长闭环。

因此，本审计优先关注以下问题：

- 首屏是否能建立信任并推动注册。
- 注册链路是否顺畅。
- 对话工作台是否符合高中生用户心智。
- 长等待、错误、空状态是否清晰可理解。
- 营销页与产品内页是否形成统一品牌体验。

## 2. 审计范围

本次审计覆盖以下前端模块：

| 模块 | 文件 | 审计重点 |
| --- | --- | --- |
| 路由结构 | `frontend/src/App.jsx` | 营销页、注册页、工作台、旧入口跳转 |
| 落地页 | `frontend/src/pages/Landing.jsx` | 首屏价值表达、导航有效性、CTA、视觉可信度 |
| 导航 | `frontend/src/components/Navbar.jsx` | 营销导航与 App 内部导航隔离 |
| 注册页 | `frontend/src/pages/Register.jsx` | 注册转化、表单密度、首屏可见性 |
| 登录页 | `frontend/src/pages/Login.jsx` | 与注册页一致性 |
| 成功页 | `frontend/src/pages/Success.jsx` | 注册后下一步引导 |
| 工作台布局 | `frontend/src/layouts/WorkspaceLayout.jsx` | Codex/ClaudeCode 式工作区结构 |
| 侧边栏 | `frontend/src/components/Sidebar.jsx` | 主导航信息架构 |
| 上下文栏 | `frontend/src/components/ContextBar.jsx` | 用户、模型、引擎状态展示 |
| 对话页 | `frontend/src/pages/Chat.jsx` | 长等待、消息流、输入区、任务提炼入口 |
| 任务页 | `frontend/src/pages/Tasks.jsx` | 空态、错误态、任务分组 |
| 打卡页 | `frontend/src/pages/CheckIn.jsx` | 与任务工作台的一致性 |
| 能力页 | `frontend/src/pages/Capabilities.jsx` | 工程控制台信息是否应暴露给学生 |
| 设置页 | `frontend/src/pages/Settings.jsx` | 系统信息展示边界 |
| 全局样式 | `frontend/src/styles/global.css` | 色彩、排版、动效、响应式、设计 token |

## 3. 审计方法与证据来源

本次审计基于三类证据：

1. 代码结构检查：阅读 React 页面、组件、路由和 CSS。
2. 本地页面运行检查：启动前端开发服务并访问关键页面。
3. DOM 与样式量化检查：检查导航锚点、首屏高度、按钮尺寸、布局宽度、状态呈现。

关键观察结果：

- Landing 页面文档高度等于桌面视口高度，实际只有 Hero 首屏。
- Landing 导航声明了多个锚点，但页面没有对应区块。
- 注册页在 1591x810 桌面视口下，提交按钮落到首屏下方。
- `/app/chat` 已进入侧边工作台结构，方向正确，但长等待态信息不足。
- `/app/capabilities` 暴露 DeerFlow skills、gateway、provider、ON/OFF 等工程信息。
- 任务页可能同时展示错误态和空态。
- 全局 CSS 有少量变量，但大部分视觉属性仍分散在具体 class 和 inline style 中。
- CSS 动效没有 `prefers-reduced-motion` 降级。
- 多处使用 `100vh`，移动端存在地址栏导致的高度跳动风险。

## 4. 设计定位判断

### 4.1 当前产品应采用的设计语言

Awaken 不是纯工具型开发者产品，也不是纯营销网站。它更接近：

> 面向高中生和家长的 AI 生涯成长产品，以“小海”作为持续陪伴式角色，通过对话和微行动形成成长闭环。

因此，合理的设计方向应是：

- 营销页：教育科技、可信、清晰、温和，重点建立信任与转化。
- 产品内页：专注工作台，但应降低工程噪声，服务“对话探索”和“微行动执行”。
- 视觉气质：克制、清爽、具有陪伴感，不使用过度炫技的 AI 紫色渐变或复杂动画。
- 信息密度：低到中等。高中生用户不应被模型、gateway、skill 开关等工程信息打断。

### 4.2 Codex / ClaudeCode 可借鉴的部分

Codex 和 ClaudeCode 的核心设计价值不是“看起来像开发者工具”，而是：

- 长任务运行时给用户持续状态反馈。
- 左侧保留稳定导航，主区域保持专注。
- 上下文状态明确，例如当前项目、模型、任务进度。
- 复杂能力被组织在后台，不直接干扰用户主要目标。

Awaken 当前 `/app/*` 工作台已经借鉴了侧栏 + 上下文栏 + 主内容区的结构，这是正确方向。但必须避免直接把“开发者控制台”作为学生产品体验呈现。

## 5. 总体评价

当前前端已经具备一个可继续演进的基础：

- 主色统一，蓝色教育科技感明确。
- Landing 使用真实学生图片，比抽象 AI 插画更可信。
- App 内部从顶部导航切换到侧边工作台，这是长期正确的方向。
- 聊天气泡、多段落渲染、任务入口已经具备 MVP 闭环雏形。

但当前影响体验的主要问题并不是“视觉不够高级”，而是信息架构和状态设计不够稳：

1. Landing 导航承诺不存在。
2. 注册页主按钮首屏不可见。
3. 学生端暴露开发者控制台。
4. DeerFlow 长等待态没有充分解释。
5. 错误态与空态混杂。
6. 营销页、工作台、打卡页像三个不同产品。

这些问题会直接影响用户信任、注册转化、对话完成率和产品心智一致性，应优先修复。

## 6. 问题分级总览

| 编号 | 优先级 | 问题 | 主要影响 |
| --- | --- | --- | --- |
| UI-001 | P0 | Landing 导航锚点不存在 | 信任下降，点击无反馈 |
| UI-002 | P0 | 注册页提交按钮首屏不可见 | 注册转化下降 |
| UI-003 | P0 | 学生端暴露 DeerFlow 能力控制台 | 产品心智错位 |
| UI-004 | P1 | 聊天长等待态信息不足 | 用户误判卡死 |
| UI-005 | P1 | 任务页错误态与空态同时出现 | 用户不知道如何恢复 |
| UI-006 | P1 | 营销页、工作台、打卡页视觉与信息架构割裂 | 产品连续性弱 |
| UI-007 | P1 | 缺少稳定设计 token，inline style 分散 | 后续维护成本升高 |
| UI-008 | P2 | 动效没有 reduced-motion 降级 | 可访问性不足 |
| UI-009 | P2 | 多处使用 `100vh` | 移动端高度跳动 |
| UI-010 | P2 | Typography 阶梯不够系统 | 层级稳定但缺少精细度 |
| UI-011 | P2 | 文案语气混杂 | 小海人格被工程语言稀释 |
| UI-012 | P2 | CTA 意图和页面路径未完全收敛 | 用户下一步不够唯一 |

## 7. 详细问题报告

### UI-001 Landing 导航锚点不存在

优先级：P0

涉及位置：

- `frontend/src/components/Navbar.jsx`
- `frontend/src/pages/Landing.jsx`

现象：

导航中存在以下入口：

- 产品原理：`#how-it-works`
- 升学顾问：`#features`
- 用户心声：`#testimonials`
- 资源中心：`#`
- 联系我们：`#`

但 Landing 页面实际只渲染了 Hero 区域，没有对应的 `id="how-it-works"`、`id="features"`、`id="testimonials"` 区块。`资源中心` 和 `联系我们` 也是空链接。

影响：

- 用户点击导航后没有信息增量，会感到页面未完成。
- 对教育和生涯规划产品而言，信任是转化前提，空导航会降低可信度。
- `探索 Awaken` CTA 指向不存在的区块，削弱二级 CTA 价值。

根因：

Landing 当前只完成了首屏视觉，没有完成导航对应的信息架构。

修复建议：

短期方案：

- 删除无效导航项，只保留 Logo、立即注册、登录。
- 删除或改写 `探索 Awaken`，避免指向不存在的锚点。

长期正确方案：

- 补齐三个轻量 section：
  - `产品如何工作`：注册、对话、微行动、打卡四步。
  - `小海如何陪你探索`：苏格拉底式提问、不会直接贴标签、会沉淀行动。
  - `为什么可以信任`：隐私边界、不会替代专业咨询、学生自主选择。

验收标准：

- 页面中所有导航链接都有真实目标。
- 点击导航后滚动到对应区块。
- 不存在 `href="#"` 的假入口。
- Landing 首屏以下至少有 2-3 个支撑注册决策的信息区块。

### UI-002 注册页提交按钮首屏不可见

优先级：P0

涉及位置：

- `frontend/src/pages/Register.jsx`
- `frontend/src/styles/global.css` 中 `.page-section`、`.form-card`、`.form-group`

现象：

当前注册页包含：

- 姓名
- 邮箱
- 年级
- 设置密码
- 确认密码
- 提交按钮
- 服务条款提示
- 登录入口
- 返回首页

在 1591x810 桌面视口下，提交按钮已经落到首屏下方。用户必须滚动才能完成注册。

影响：

- 注册转化路径被拉长。
- 用户在填写密码后不能立即看到主动作。
- 对 MVP 来说，注册进入对话是核心链路，首屏不可提交是直接损害。

根因：

早期注册页可能只有少量字段，后来增加密码字段后，页面布局仍沿用窄单列表单，没有重新调整信息密度。

修复建议：

桌面端：

- 改为左右分栏布局。
- 左侧：价值说明、小海介绍、隐私/安全承诺。
- 右侧：表单卡片。
- 控制表单卡片高度，确保提交按钮在首屏内。

移动端：

- 保持单列。
- 标题文案缩短。
- 表单间距从 24px 降到 16-18px。

内容策略：

- 主按钮文案建议改为 `开始和小海对话` 或 `创建账号并进入对话`，比 `免费注册开始体验` 更具体。
- 服务条款和隐私政策应作为弱提示，不抢占核心区域。

验收标准：

- 1366x768 桌面视口下，提交按钮可见。
- 390x844 移动端下，首屏至少可见前三个字段，滚动距离合理。
- 表单错误提示出现时不导致布局严重跳动。

### UI-003 学生端暴露 DeerFlow 能力控制台

优先级：P0

涉及位置：

- `frontend/src/App.jsx`
- `frontend/src/components/Sidebar.jsx`
- `frontend/src/pages/Capabilities.jsx`

现象：

学生主导航中包含 `能力 DeerFlow`。进入后页面展示：

- DeerFlow 在线状态
- 当前模型
- Skills 数量
- Skills 开关
- ON/OFF 控件
- 英文 skill 描述
- `gateway`
- `provider 未返回`

影响：

- 高中生用户不需要理解模型、skill、gateway。
- 工程控制台语言会削弱“小海”作为成长伙伴的温度。
- 用户可能误操作能力开关，影响对话质量。
- 产品定位从“学生成长工具”偏移到“AI 调试平台”。

根因：

DeerFlow 调试需求被直接放入学生主导航，没有区分内部运营/开发者视图与学生视图。

修复建议：

短期方案：

- 从 `Sidebar` 的学生主导航中移除 `能力`。
- 保留 `/app/capabilities` 路由，但不展示在导航中。

中期方案：

- 增加内部调试入口，例如 `/app/admin/capabilities`。
- 仅开发环境或管理员身份可见。
- 将 `Settings` 中的工程信息也收敛为只读状态，不面向学生强调。

学生端替代表达：

- `小海状态：可用`
- `联网资料：可用`
- `任务生成：可用`
- 不展示 `skill name`、`provider`、`assistant_id`。

验收标准：

- 学生主导航只保留与用户目标相关的入口。
- 普通学生路径不会看到 skill 开关。
- 内部调试页仍可通过明确路径访问，满足开发联调需求。

### UI-004 聊天长等待态信息不足

优先级：P1

涉及位置：

- `frontend/src/pages/Chat.jsx`
- `frontend/src/styles/global.css`

现象：

当 DeerFlow 响应较慢时，界面展示：

- 小海正在思考
- 输入框禁用
- 发送按钮禁用

但没有说明：

- 为什么等待。
- 大约需要多久。
- 用户是否可以取消。
- 网络搜索或模型推理是否仍在进行。
- 失败后如何恢复。

影响：

- 用户等待超过 8-10 秒会怀疑页面卡死。
- DeepSeek/DeerFlow 响应可能达到几十秒，该状态不是边缘场景，而是常见路径。
- 输入框禁用但没有解释，会削弱控制感。

根因：

等待态被当作普通聊天 typing indicator，而不是长任务状态。

修复建议：

状态文案：

- 初始 0-5 秒：`小海正在整理你的回答...`
- 5-15 秒：`正在结合你的信息思考方向，可能还需要几秒。`
- 15 秒以上：`这次分析比较深入，你可以继续等待，或稍后重试。`

交互能力：

- 增加 `取消生成`。
- 增加 `重试`。
- 如果后端支持，优先接入流式输出。
- 如果后端无法流式，至少提供阶段性状态说明。

视觉建议：

- 不只显示一个小气泡。
- 可以使用轻量状态卡，展示“正在分析兴趣线索 / 正在生成下一步问题 / 正在整理微行动”。

验收标准：

- 用户等待 15 秒时仍能明确知道系统没有卡死。
- 失败时有明确恢复路径。
- 输入框 disabled 状态有可见说明。

### UI-005 任务页错误态与空态同时出现

优先级：P1

涉及位置：

- `frontend/src/pages/Tasks.jsx`

现象：

当任务同步失败时，页面可能同时出现：

- `任务同步失败`
- `学生不存在`
- `还没有微行动任务`

影响：

用户无法判断当前状态：

- 是账号不存在？
- 是接口失败？
- 是真的没有任务？
- 是需要重新登录？

根因：

`error` 与 `totalCount === 0` 的渲染逻辑没有互斥。

修复建议：

状态优先级应固定为：

1. loading
2. 未登录或无 email
3. error
4. empty
5. has data

如果存在 `error`，不要继续展示空态。

错误态应给出具体动作：

- `重新登录`
- `回到对话区`
- `刷新重试`

验收标准：

- 同一屏不会同时出现错误态和空态。
- 每个状态都只有一个主 CTA。
- 错误态能解释用户下一步。

### UI-006 营销页、工作台、打卡页体验割裂

优先级：P1

涉及位置：

- `frontend/src/pages/Landing.jsx`
- `frontend/src/pages/Register.jsx`
- `frontend/src/pages/Success.jsx`
- `frontend/src/pages/CheckIn.jsx`
- `frontend/src/layouts/WorkspaceLayout.jsx`
- `frontend/src/App.jsx`

现象：

当前存在三套页面语言：

1. Landing/Register：传统顶部导航 + 单页营销风格。
2. `/app/*`：侧边栏工作台。
3. CheckIn：独立顶部 Logo + 窄表单卡片。

影响：

- 用户从注册到对话像进入了另一个产品。
- 任务列表在工作台里，任务打卡却跳出工作台。
- 信息架构不连续，用户不知道自己还在同一个成长空间中。

根因：

工作台改版只覆盖了 `/app/chat`、`/app/tasks`、`/app/capabilities`、`/app/settings`，没有覆盖打卡链路和注册后链路。

修复建议：

- 将 CheckIn 纳入 WorkspaceLayout，例如 `/app/checkin?task_id=...`。
- 保留 `/checkin` 作为旧链接兼容重定向。
- Success 页的主 CTA 直接进入 `/app/chat`。
- 注册、登录可以暂时保留营销布局，但视觉 token 应与工作台统一。

验收标准：

- 用户接受任务后进入的打卡页仍在工作台框架中。
- 工作台内主导航始终可见或移动端可呼出。
- 注册成功后的路径统一进入 `/app/chat`。

### UI-007 缺少稳定设计 token，样式分散

优先级：P1

涉及位置：

- `frontend/src/styles/global.css`
- 多个页面中的 inline style

现象：

当前 CSS 中已有少量变量：

- `--awaken-blue`
- `--awaken-blue-strong`
- `--workspace-ink`
- `--workspace-muted`
- `--workspace-border`
- `--workspace-surface`
- `--workspace-canvas`

但大量样式仍散落在具体 class 中：

- 颜色重复硬编码。
- 阴影重复硬编码。
- 圆角尺度不完全统一。
- inline style 出现在 Register、Login、Success、CheckIn 等页面。

影响：

- 继续增加页面时视觉一致性会恶化。
- 修改品牌色、卡片样式、状态色的成本高。
- 设计系统无法沉淀。

修复建议：

建立最小语义 token，不引入大型设计系统：

```css
:root {
  --color-accent: #1f6fe5;
  --color-accent-strong: #1250b8;
  --color-text-primary: #12213f;
  --color-text-secondary: #4b5563;
  --color-text-muted: #6b7280;
  --color-surface-page: #f8f8fb;
  --color-surface-card: rgba(255, 255, 255, 0.84);
  --color-border-subtle: rgba(203, 213, 225, 0.88);
  --color-danger: #dc2626;
  --color-success: #15803d;
  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-pill: 999px;
  --shadow-card: 0 18px 52px rgba(15, 23, 42, 0.07);
}
```

清理顺序：

1. 先清理按钮。
2. 再清理表单。
3. 再清理卡片。
4. 最后清理状态提示。

验收标准：

- 新增页面不再直接写大段 inline style。
- 主色、状态色、圆角、阴影有统一变量来源。
- 同类按钮在 Landing、Register、Workspace 中视觉一致。

### UI-008 动效没有 reduced-motion 降级

优先级：P2

涉及位置：

- `frontend/src/styles/global.css`

现象：

当前 CSS 中存在：

- `fadeUp`
- `floatIn`
- `scaleIn`
- `slideIn`
- `bubbleIn`
- `chatBounce`

但没有 `prefers-reduced-motion` 降级。

影响：

- 对动效敏感用户不友好。
- 聊天等待点动画属于可能持续循环的动效，应允许关闭。
- 不符合基础可访问性要求。

修复建议：

增加全局降级：

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
```

验收标准：

- 系统开启减少动态效果后，页面不再播放入场动画和循环跳点动画。
- 基础交互仍可用。

### UI-009 多处使用 `100vh`，移动端存在高度风险

优先级：P2

涉及位置：

- `frontend/src/styles/global.css`

现象：

多处布局使用：

- `min-height: 100vh`
- `height: 100vh`
- `min-height: calc(100vh - 66px)`

影响：

- iOS Safari 和移动端浏览器地址栏展开/收起时，`100vh` 可能导致页面高度跳动。
- 聊天输入区可能被浏览器 UI 或键盘影响。

修复建议：

- App shell 改为 `100dvh`。
- Sidebar 改为 `height: 100dvh`。
- Chat page 改为 `min-height: calc(100dvh - 64px)`。
- 输入区底部加入安全区 padding：

```css
.chat-input-bar {
  margin-bottom: env(safe-area-inset-bottom);
}
```

验收标准：

- 移动端打开聊天页，输入区不会因地址栏变化明显跳动。
- 键盘弹出后仍可看到输入区域。

### UI-010 Typography 阶梯不够系统

优先级：P2

涉及位置：

- `frontend/src/styles/global.css`

现象：

当前字体整体可读，但字号和字重主要按页面局部手写：

- Landing H1：60px
- Page title：42px
- Chat title：26px
- Workspace h2：30px
- Context h1：18px
- 多处 15px、15.5px、17px、18px 混用

影响：

- 页面之间层级基本可用，但缺少统一节奏。
- 后续页面增加后，视觉层级容易漂移。

修复建议：

建立最小字号阶梯：

| Token | 建议值 | 用途 |
| --- | --- | --- |
| `--font-display` | 56-60px | Landing H1 |
| `--font-page-title` | 30-36px | 页面主标题 |
| `--font-section-title` | 22-26px | 卡片/模块标题 |
| `--font-body` | 15-16px | 正文 |
| `--font-caption` | 12-13px | 辅助文字 |

中文文本不需要盲目追求英文字体，系统中文无衬线足够。重点是统一字号、行高和字重。

验收标准：

- 同级标题在不同页面视觉一致。
- 正文行高稳定在 1.55-1.7。
- 辅助文字不低于可读对比度。

### UI-011 文案语气混杂

优先级：P2

涉及位置：

- `frontend/src/pages/Capabilities.jsx`
- `frontend/src/pages/Settings.jsx`
- `frontend/src/components/ContextBar.jsx`

现象：

当前学生路径中混入大量工程表达：

- `DeerFlow gateway`
- `skills`
- `provider 未返回`
- `assistant_id`
- `模型列表`
- `由 /deerflow/status 或模型列表推断`

这些表达与小海的陪伴式语言不一致。

影响：

- 产品人格不稳定。
- 学生用户理解成本高。
- 家长用户可能质疑产品是否成熟。

修复建议：

学生端语言：

- `小海状态`
- `资料检索`
- `任务生成`
- `当前可用`
- `暂时不可用`

内部调试语言：

- 保留 `DeerFlow`、`assistant_id`、`model`、`skills`，但只在开发者/管理员视图出现。

验收标准：

- 学生主流程中不出现 `gateway`、`provider`、`skill` 等工程词。
- 所有错误提示都说明“用户下一步该做什么”。

### UI-012 CTA 意图和页面路径未完全收敛

优先级：P2

涉及位置：

- `frontend/src/pages/Landing.jsx`
- `frontend/src/pages/Register.jsx`
- `frontend/src/pages/Success.jsx`
- `frontend/src/pages/CheckIn.jsx`

现象：

页面中存在多个类似但不完全一致的动作：

- 免费注册
- 立即注册
- 免费注册开始体验
- 开始与小海对话
- 探索 Awaken
- 还没注册？立即加入 Awaken
- 查看演示：打卡页面

影响：

- 用户的主路径不够唯一。
- 演示入口暴露在真实注册成功页中可能分散注意力。

修复建议：

主路径统一：

- Landing 主 CTA：`开始和小海对话`
- 注册提交：`创建账号并进入对话`
- Success 主 CTA：`进入对话工作区`
- 任务空态 CTA：`去和小海聊聊`

弱入口：

- 演示入口只在开发环境或测试页面展示。
- 返回首页不应与主 CTA 视觉竞争。

验收标准：

- 每个页面只有一个主 CTA。
- 相同意图使用同一套文案。
- 注册成功后默认进入 App 工作台。

## 8. 推荐修复路线

### Phase 1：先修链路信任和转化

目标：解决 P0 问题，不追求大改版。

任务：

1. Landing 删除或补齐无效导航锚点。
2. 注册页重排，确保提交按钮首屏可见。
3. 学生侧边栏移除 `Capabilities`。
4. Success 主 CTA 改为进入 `/app/chat`。

建议工期：0.5-1 天。

验证：

- `npm run build`
- 手动检查 `/`、`/register`、`/success`、`/app/chat`
- 点击所有导航链接，确认无空链接。

### Phase 2：修复关键状态体验

目标：让慢响应、错误、空态都可理解。

任务：

1. 增强聊天长等待态。
2. 任务页错误态与空态互斥。
3. 对话失败时提供重试入口。
4. 检查 Login/Register 表单错误提示一致性。

建议工期：1 天。

验证：

- 模拟 DeerFlow 慢响应。
- 模拟学生不存在。
- 模拟未登录进入任务页。
- 模拟接口失败。

### Phase 3：统一 App 内部信息架构

目标：让“对话 → 任务 → 打卡”成为一个连续工作区。

任务：

1. 将 CheckIn 纳入 WorkspaceLayout。
2. `/checkin` 保留旧入口兼容，重定向到 `/app/checkin`。
3. 侧边栏只保留学生目标相关入口。
4. Settings 中工程信息降噪。

建议工期：1-2 天。

验证：

- 从 Chat 接受任务进入 CheckIn。
- 从 Tasks 点击去打卡。
- 移动端侧栏打开/关闭。

### Phase 4：沉淀最小设计系统

目标：降低后续迭代成本。

任务：

1. 建立颜色、圆角、阴影、字号 token。
2. 清理 inline style。
3. 统一按钮、表单、卡片、状态提示。
4. 增加 reduced-motion。
5. `100vh` 改为 `100dvh`。

建议工期：1-2 天。

验证：

- `npm run build`
- 桌面端 1366x768
- 移动端 390x844
- 系统开启 reduced motion

## 9. 验收清单

### 9.1 Landing

- [ ] 所有导航链接都有真实目标。
- [ ] 首屏 H1、描述、主 CTA、视觉图都在首屏内。
- [ ] 不存在 `href="#"` 假入口。
- [ ] 首屏下方有支撑信任的内容区块。

### 9.2 注册与登录

- [ ] 1366x768 下注册提交按钮首屏可见。
- [ ] 表单错误提示不会遮挡主按钮。
- [ ] 主 CTA 文案明确指向“进入对话”。
- [ ] 注册、登录、成功页视觉 token 一致。

### 9.3 工作台

- [ ] 学生侧栏不展示 DeerFlow 能力控制台。
- [ ] Chat、Tasks、CheckIn 在同一工作台内。
- [ ] ContextBar 只展示用户能理解的状态。
- [ ] 移动端侧栏可打开、关闭，遮罩可点击关闭。

### 9.4 聊天

- [ ] 等待超过 10 秒时，有明确说明。
- [ ] 请求失败后有重试路径。
- [ ] 输入框 disabled 时原因可见。
- [ ] 多段落回复排版正常。

### 9.5 任务

- [ ] loading、未登录、error、empty、data 五种状态互斥。
- [ ] 错误态只展示错误恢复路径，不混入空态。
- [ ] 空态有唯一主 CTA。
- [ ] 打卡入口路径一致。

### 9.6 可访问性与响应式

- [ ] 添加 `prefers-reduced-motion` 降级。
- [ ] App shell 使用 `100dvh`。
- [ ] 移动端输入区不被底部安全区遮挡。
- [ ] 按钮文本对比度满足基础可读性。

## 10. 不建议优先做的事情

以下事项短期不应优先：

1. 不建议先换整套 UI 框架。
   - 当前问题主要是信息架构和状态体验，不是组件库缺失。

2. 不建议先做大面积动效。
   - DeerFlow 慢响应时更需要清楚的状态反馈，而不是更多动画。

3. 不建议把 Capabilities 包装得更漂亮后继续给学生看。
   - 问题不是样式，而是它不应该出现在学生主流程。

4. 不建议新增大量营销内容。
   - Landing 需要补齐信任区块，但应保持克制，优先解释核心闭环。

5. 不建议在鉴权未完全收敛前强化个人数据展示。
   - 当前项目仍有部分业务接口未强制 token 校验，学生端不应展示过多敏感个人信息。

## 11. 推荐目标形态

### 11.1 营销页目标形态

结构建议：

1. Hero：一句话价值 + 主 CTA + 学生真实场景图。
2. 工作原理：注册、对话、微行动、打卡。
3. 小海体验：展示一段简短对话示例。
4. 微行动示例：展示任务如何足够小、当天可完成。
5. 信任说明：隐私、安全、AI 不替代专业咨询。
6. 最终 CTA：开始和小海对话。

### 11.2 App 工作台目标形态

侧边栏建议：

- 对话
- 微行动
- 成长记录
- 设置

不建议学生侧边栏展示：

- 能力
- 模型
- Skills
- Gateway
- Provider

### 11.3 聊天页目标形态

聊天页应支持三种核心状态：

1. 普通对话：消息流 + 输入框。
2. 深度思考：明确说明等待原因和预计时间。
3. 可提炼任务：轻量提示卡 + 单一主 CTA。

### 11.4 任务页目标形态

任务页应围绕学生行动，而不是任务管理系统：

- 今天要做什么。
- 为什么做这个。
- 预计花多久。
- 做完后记录什么。
- 已完成后看见成长反馈。

## 12. 结论

Awaken 当前前端已经有一个可用基础，但需要把“技术原型”收敛为“学生成长产品”。最重要的修复不是视觉装饰，而是四个结构问题：

1. 修复 Landing 空导航，补齐信任信息。
2. 让注册主按钮首屏可见，提高转化。
3. 把 DeerFlow 能力控制台移出学生主流程。
4. 强化慢响应和错误状态，让用户知道系统正在做什么、失败后该怎么办。

完成这些后，再做设计 token、响应式和动效降级，前端质量会进入一个更稳定、可长期迭代的状态。
