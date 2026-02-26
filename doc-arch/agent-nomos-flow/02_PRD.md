# Product Requirements Document (PRD)

**Document Version:** 1.0
**Last Updated:** 2026-02-23
**Status:** DRAFT

---

## 1. Product Vision

### 1.1 Vision Statement

构建一个刚性、可靠的 AI Agent 编码工作流框架,将代码质量管控从"软约束"转变为"物理定律",通过 Why-First 机制强制深度思考,确保 AI Agent 生成的代码始终符合工程规范、安全标准和业务规则。同时通过标注循环、阶段门控、项目知识累积和自动化工具链,实现人机协作效率的指数级提升,让人类专注于"为什么"的高阶决策,Agent 专注于"怎么做"的执行细节。

### 1.2 Value Proposition

**核心价值主张:**

1. **刚性质量保证**: Linter 作为"物理定律",Agent 即使"幻觉"也无法突破安全与质量底线,代码质量从"靠自觉"变成"物理强制"

2. **标注循环前置 review**: 把 code review 前置到写代码之前,在 plan.md 里批注比聊天高效 10 倍,上下文永不丢失

3. **零上下文污染**: Task 文件夹隔离,每个迭代纯净独立,支持并行开发,人类只需专注当前任务

4. **人类价值放大**: 人类只做高阶批注和决策,不用盯聊天记录追上下文,Agent 被物理约束在正确轨道

5. **速度与质量双提升**: 所有"幻觉""跳步""增量修补"在 Hooks 层被物理消灭,Agent 编码从"需要盯紧"变成"可以放心睡觉"

6. **可插拔扩展**: BaseRule 接口 + 流水线模式,用户可"搭积木"式添加业务规则,第一二层开箱即用,第三层自由定制

7. **果断 revert 节省成本**: 方向错了直接回滚,比精心 patch 节省 token 和时间,90% 的浪费被避免

8. **跨会话持久**: 状态在 MD 文件里积累,支持单长会话或中途关闭重开,SessionStart Hook 自动恢复

9. **Why-First 深度思考**: 强制 Agent 在动手前深度思考"为什么",避免"想当然",方案更合理

10. **项目知识累积**: project-why.md 作为跨任务知识库,避免重复提问,项目智慧持续沉淀

11. **人机分工明确**: 人类负责"为什么"和决策,Agent 负责"怎么做"和执行,各司其职,效率最大化

12. **可视化设计**: Mermaid 图自动生成,复杂架构一目了然,沟通成本降低 80%

13. **Test-First 质量保证**: 强制 TDD,测试覆盖率和质量显著提升

14. **失败学习闭环**: 失败经验自动沉淀到 project-why.md,避免重复犯错

15. **PR 自动化**: 自动生成 PR 描述,节省人工整理时间

16. **多任务分支切换**: 独立 task 文件夹 + 分支切换,多任务互不干扰

17. **成就系统激励**: Gamification 提升使用体验,Agent "成长"可见

18. **一键调用**: SKILL 封装完整流程,用户只需 /nomos,降低使用门槛

**差异化优势:**
- 基于 2026 年 Claude Code 生态最佳实践,生产级可用
- 深度绑定 Claude Code Hooks 机制,充分利用其原生能力,实现真正的"物理门控"
- 专为 Claude Code 设计,不追求通用性,确保最佳性能和可靠性
- Why-First 机制确保方案合理性,避免"想当然"
- project-why.md 知识库实现项目智慧累积,越用越聪明
- SKILL Marketplace 模式支持可组合的技能生态

---

## 2. Problem Statement

### 2.1 Current State

当前 AI Agent 编码工具普遍存在以下问题:
- Agent 依赖 prompt 软约束,容易"想当然"跳过需求分析
- 对话式交互导致上下文丢失,人类需要反复解释
- Code review 滞后,问题发现在代码生成之后
- 缺乏强制执行的质量门控机制
- 多次迭代需求容易混淆,状态管理混乱

### 2.2 Pain Points

**P1 - 方向错误的高成本:**
AI Agent 生成代码时容易"想当然",跳过需求分析直接写代码,导致方向错误后花三倍时间增量修补

**P2 - 软约束无效:**
LLM 的生成自由度(Soft constraints)与软件工程的确定性(Hard constraints)之间缺乏自动化治理防火墙

**P3 - 架构破坏:**
Agent 生成的代码容易违反架构规范(如直接访问 DB、破坏分层隔离),导致后期无法替换底层服务

**P4 - Linter 形同虚设:**
传统 Linter 只是"建议",Agent 可能忽略,缺乏强制执行机制

**P5 - 上下文丢失:**
对话式交互容易丢失上下文,人类需要反复解释需求和约束,效率低下

**P6 - Review 滞后:**
Agent 生成代码后才发现问题,code review 滞后,浪费 token 和时间

**P7 - 业务规则缺失:**
每个公司/行业有特定业务规则(如金融必须用 Decimal、多租户必须带 tenant_id),通用 Linter 无法覆盖

**P8 - 需求串扰:**
多次迭代需求容易"串",旧任务的分析和计划混在一起,Agent 分不清边界

**P9 - 黑盒代码:**
Agent 容易生成"黑盒代码"(无日志、无监控),生产出问题难以追踪

**P10 - 增量修补陷阱:**
90% 的人舍不得删除已生成的错误代码,倾向于增量修补而非果断 revert,越改越乱

### 2.3 Impact

**不解决这些问题的后果:**
- 开发效率低下,Agent 生成的代码需要大量人工返工
- 代码质量无法保证,生产环境频繁出现 bug
- 技术债务累积,架构逐渐腐化
- 团队协作困难,每个人都在"救火"
- AI Agent 工具的价值大打折扣,甚至成为负担

---

## 3. User Personas

### 3.1 Primary Users

| Persona | Description | Goals | Pain Points |
|---------|-------------|-------|-------------|
| **Claude Code 用户** | 使用 Claude Code 进行 AI 辅助编码的开发者 | 希望 Agent 生成的代码质量可控、符合规范、减少返工 | Agent 经常违反架构规则,需要手动检查和修复 |
| **技术团队 Leader** | 负责代码质量和架构治理的技术负责人 | 确保团队使用 Claude Code 时不破坏现有架构,保持代码质量 | 缺乏对 Agent 生成代码的强制管控手段 |
| **企业架构师** | 定义和维护企业级架构规范和业务规则 | 将公司特定的架构约束和业务规则自动化执行 | 通用 Linter 无法覆盖业务特定规则 |
| **独立开发者** | 使用 Claude Code 提升个人开发效率的程序员 | 快速开发的同时保证代码质量,减少后期维护成本 | Agent 生成代码质量不稳定,需要频繁 review |

---

## 4. User Stories

### 4.1 Core Features

- **US-001:** 作为 Claude Code 用户,我希望能定义刚性 Linter 规则,使得 Agent 生成的代码必须通过检查才能写入文件,这样可以从源头保证代码质量

- **US-002:** 作为技术 Leader,我希望能在 plan.md 文件里直接批注和审查 Agent 的计划,而不是在聊天里来回沟通,这样可以保持完整上下文并提高效率

- **US-003:** 作为企业架构师,我希望能通过 BaseRule 接口自定义业务规则(如模块隔离、i18n、logger),并让这些规则自动执行,这样可以确保所有代码符合公司规范

- **US-004:** 作为独立开发者,我希望每个任务有独立的文件夹(research/plan/code_review.md),避免不同需求混在一起,这样可以专注当前任务

- **US-005:** 作为 Claude Code 用户,我希望 Agent 在写代码前必须先完成需求分析和计划审查,通过阶段门控强制执行,这样可以避免"想当然"就开干

### 4.2 Secondary Features

- **US-101:** 作为技术 Leader,我希望当 Agent 生成的代码方向错误时,系统能自动 git revert 并回到计划阶段,而不是在错误基础上打补丁

- **US-102:** 作为企业架构师,我希望能从 plan.md 动态读取本次迭代的特殊规则(如本次必须用 customT() 而不是 t()),实现"标注即拦截"

- **US-103:** 作为独立开发者,我希望 Linter 检查失败时,错误消息能直接喂回 Agent 并提供修复建议,让 Agent 自动修复而不是手动干预

- **US-104:** 作为 Claude Code 用户,我希望在每个任务开始前,系统能通过苏格拉底式提问强制 Agent 深度思考"为什么",避免方案不合理

- **US-105:** 作为技术 Leader,我希望项目知识能累积到 project-why.md,避免每次都重新解释相同的概念和约束

- **US-106:** 作为独立开发者,我希望 Agent 能自动生成 Mermaid 流程图,让我快速理解复杂的设计方案

- **US-118:** 作为 Claude Code 用户,我希望能通过浏览器查看和标注 plan.md,无需依赖 IDE,支持 Markdown/Mermaid 渲染和在线标注

- **US-119:** 作为独立开发者,我希望任务目录使用短 ID(如 t1, t2)简化引用,同时目录名包含短 ID 确保可见性

- **US-120:** 作为技术 Leader,我希望 Task Viewer 服务器能自动关闭(超时或浏览器关闭),避免资源占用

- **US-121:** 作为 Claude Code 用户,我希望能同时打开多个任务查看器,系统自动分配可用端口避免冲突

- **US-107:** 作为技术 Leader,我希望系统能强制 Test-First,确保 Agent 先写测试再写代码

- **US-108:** 作为企业架构师,我希望所有失败经验(Linter 失败、测试失败、revert)都能自动记录,形成失败知识库

- **US-109:** 作为独立开发者,我希望任务完成后能自动生成 PR 描述,节省整理时间

- **US-110:** 作为 Claude Code 用户,我希望能通过 /nomos 一键调用完整工作流,而不需要手动配置复杂的 Hooks

- **US-111:** 作为 Claude Code 用户,我希望系统能记住我当前正在进行的任务,重启会话后自动提示而不是盲目加载

- **US-112:** 作为技术 Leader,我希望能通过 /nomos:switch-task 快速切换任务,系统自动加载对应的上下文

- **US-113:** 作为独立开发者,我希望能通过 /nomos:list-tasks 查看所有任务的状态,方便管理多个并行任务

- **US-114:** 作为 Claude Code 用户,我希望系统能智能检测我的任务切换意图(如"继续 XXX 任务"),自动加载上下文而不需要手动命令

- **US-115:** 作为技术 Leader,我希望 Agent 在标注循环中遇到不理解的批注时能诚实提问,而不是自以为是地猜测,确保真正的理解对齐

- **US-116:** 作为企业架构师,我希望 project-why.md 更新时能自动检测相似内容并合并,避免知识重复和碎片化

- **US-117:** 作为独立开发者,我希望更新 project-why.md 时系统能先展示相关的已有知识,让我确认是否需要合并或补充

- **US-122:** 作为 Claude Code 用户,我希望能右键点击文档行创建标注,左键点击标记点查看历史,操作直观高效

- **US-123:** 作为技术 Leader,我希望标注历史能持久化保存,包括用户标注、Agent 回复、AI 追问,支持跨会话追溯

- **US-124:** 作为独立开发者,我希望 Agent 有不理解的地方时能主动追问,而不是猜测,状态用紫色闪烁提示

- **US-125:** 作为 Claude Code 用户,我希望标注代码块和 Mermaid 图时有专门的定位方式,或切换到源码视图精确定位

- **US-126:** 作为技术 Leader,我希望 Agent 修改文档后 Task Viewer 自动刷新,保留我打开的标注框状态

- **US-127:** 作为独立开发者,我希望每个 Gate 完成后自动 commit,message 包含 Gate 标记,方便追溯和 revert

- **US-128:** 作为企业架构师,我希望 commit message 有统一格式,包含类型、范围、描述和 Gate 编号

- **US-129:** 作为独立开发者,我希望任务完成后能一键生成 PR,自动从 plan.md 和 code_review.md 提取内容

- **US-130:** 作为 Claude Code 用户,我希望在需求模糊时能通过 /nomos:clarify 先澄清需求,避免调研走偏浪费时

- **US-131:** 作为独立开发者,我希望 clarify 只是轻量级对话,不生成文件,确认后再用 /nomos:start 正式开始

- **US-132:** 作为技术 Leader,我希望 clarify 能借鉴 doc-architect 的结构化思维,帮助用户从模糊想法中提取关键词、痛点、约束

---

## 5. Functional Requirements

### 5.1 Must Have Requirements

| ID | Requirement | Priority | 设计状态 |
|----|-------------|----------|----------|
| FR-001 | 系统应提供 BaseRule 标准接口,支持用户自定义 Linter 规则 | P0 | ✅ 已设计 (arch 3.3) |
| FR-002 | 系统应提供 AgentLinterEngine 核心引擎,支持规则流水线执行 | P0 | ✅ 已设计 (arch 3.3) |
| FR-003 | 系统应支持 PreToolUse Hook,在代码写入前强制执行 Linter 检查 | P0 | ✅ 已设计 (arch 3.2 + 3.10.1) |
| FR-004 | 系统应支持 Task 文件夹隔离,每个任务独立的 research/plan/code_review.md | P0 | ✅ 已设计 (arch 3.4) |
| FR-005 | 系统应支持标注循环,人类可在 plan.md 的 Review Comments 节直接批注 | P0 | ✅ 已设计 (arch 3.10) |
| FR-006 | 系统应支持阶段门控,通过 Stop Hook 验证 Phase Gates 全部通过才允许结束 | P0 | ✅ 已设计 (arch 3.2) |
| FR-007 | 系统应提供第一层规则(语法/风格),封装 Ruff/ESLint 等成熟工具 | P0 | ✅ 已设计 (arch 3.3) |
| FR-008 | 系统应提供第二层规则(安全),封装 Bandit/Semgrep 等安全扫描工具 | P0 | ✅ 已设计 (arch 3.3) |
| FR-009 | 系统应输出 JSON 格式的 Linter 报告,包含 line/message/suggestion 字段 | P0 | ✅ 已设计 (arch 3.3) |
| FR-010 | 系统应支持 Validator Subagent,只读审查 plan.md 并写回 Review Comments | P0 | ✅ 已设计 (arch 3.5 + 3.10.1) |
| FR-011 | 系统应支持 Why-First 阶段,通过苏格拉底式提问(5-12 个问题)强制深度思考 | P0 | ✅ 已设计 (arch 3.1) |
| FR-012 | 系统应提供 project-why.md 知识库,跨任务累积项目知识和失败经验 | P0 | ✅ 已设计 (arch 3.1) |
| FR-013 | 系统应支持 Mermaid 图自动生成,在 plan.md 中嵌入流程图/架构图,通过 Task Viewer HTML 界面自动渲染 | P0 | ✅ 已设计 (arch 3.7 + 2.2) |
| FR-014 | 系统应支持 Test-First 检查,PreToolUse Hook 验证测试文件存在才允许写代码 | P0 | ✅ 已设计 (arch 3.8) |
| FR-015 | 系统应支持 SKILL 封装,提供 /nomos 一键调用完整工作流 | P0 | ✅ 已设计 (arch 1.1 SKILL 编排层) |
| FR-016 | 系统应支持 .claude/current-task.txt 状态文件,记录当前活跃任务路径 | P0 | ✅ 已设计 (arch 3.4) |
| FR-017 | 系统应支持 SessionStart Hook 轻量级提示,显示当前任务而不注入完整文档 | P0 | ✅ 已设计 (arch 3.2) |
| FR-018 | 系统应支持 UserPromptSubmit Hook 智能检测,识别任务切换意图并按需注入上下文 | P0 | ✅ 已设计 (arch 3.2) |
| FR-019 | 系统应提供 /nomos:switch-task 子命令,支持显式任务切换 | P0 | ✅ 已设计 (arch 3.6.4) |
| FR-020 | 系统应提供 /nomos:list-tasks 子命令,列出所有任务及状态 | P0 | ✅ 已设计 (arch 3.11) |
| FR-021 | 系统应支持诚实追问机制,Agent 遇到不理解的批注时必须提问而非迎合 | P0 | ✅ 已设计 (arch 3.10.6) |
| FR-022 | 系统应支持 project-why.md 智能维护,更新时回顾已有内容并进行相似检测、合并、补充和增强 | P0 | ✅ 已设计 (arch 3.12) |
| FR-023 | 系统应提供 Task Viewer HTML 界面,支持浏览器查看和标注 plan.md | P0 | ✅ 已设计 (arch 2.x 整节) |
| FR-024 | 系统应支持短 ID 映射系统,任务目录格式为 tasks/t1-YYYY-MM-DD-feature/ | P0 | ✅ 已设计 (arch 2.4) |
| FR-025 | 系统应支持 Python 后端服务器自动关闭(超时 30 分钟或浏览器关闭通知) | P0 | ✅ 已设计 (arch 2.1 + 2.3) |
| FR-026 | 系统应支持动态端口分配,从 8765 开始自动检测并分配可用端口 | P0 | ✅ 已设计 (arch 2.1 + 2.3) |
| FR-027 | 系统应在 tasks/t1-xxx/.task-viewer.html 生成 HTML 界面文件 | P0 | ✅ 已设计 (arch 2.1) |
| FR-028 | 系统应通过 CDN 引入 marked.js 和 mermaid.js 实现 Markdown/Mermaid 渲染 | P0 | ✅ 已设计 (arch 2.2) |
| FR-029 | 系统应支持标注格式与现有 Review Comments 格式一致 | P0 | ✅ 已设计 (arch 3.10.2) |
| FR-030 | 系统应支持右键点击行创建新标注,左键点击标记点查看历史 | P0 | ✅ 已设计 (arch 2.5.1) |
| FR-031 | 系统应支持标注历史持久化,包含用户标注/Agent回复/AI追问的完整线程 | P0 | ✅ 已设计 (arch 2.5.2) |
| FR-032 | 系统应支持 pending_ai_question 状态,紫色闪烁图标提示用户 | P0 | ✅ 已设计 (arch 2.5.3 + 2.5.6) |
| FR-033 | 系统应支持 Markdown 特殊格式标注(代码块/Mermaid/表格)的块级定位 | P0 | ✅ 已设计 (arch 2.5.4) |
| FR-034 | 系统应支持渲染视图和源码视图切换,解决特殊格式标注定位问题 | P0 | ✅ 已设计 (arch 2.5.4) |
| FR-035 | 系统应支持内容动态刷新,Agent 修改后自动更新,保留标注框状态 | P0 | ✅ 已设计 (arch 2.5.5) |
| FR-036 | 系统应支持每个 Gate 完成后自动 commit,message 包含 #gate-X.Y 标记 | P0 | ✅ 已设计 (arch 3.6.5) |
| FR-037 | 系统应支持 commit message 规范: <type>(<scope>): <desc> #gate-X.Y | P0 | ✅ 已设计 (arch 3.6.2) |
| FR-038 | 系统应支持 PR 描述自动生成,从 plan.md 和 code_review.md 提取内容 | P0 | ✅ 已设计 (arch 3.6.6) |

### 5.2 Should Have Requirements

| ID | Requirement | Priority | 设计状态 |
|----|-------------|----------|----------|
| FR-101 | 系统应支持 Tree-sitter 多语言 AST 解析,覆盖 Python/JS/TS/Java/Go 等 | P1 | ✅ 已设计 (arch 3.13) |
| FR-102 | 系统应支持 Command + Prompt + Agent 混合 Handler,静态+语义+深度验证 | P1 | ✅ 已设计 (arch 3.2) |
| FR-103 | 系统应支持从 plan.md 动态读取本次迭代特定规则,实现"标注即拦截" | P1 | ✅ 已设计 (arch 3.10.4) |
| FR-104 | 系统应支持果断 revert 机制,Hook 检测方向错误时自动 git revert | P1 | ✅ 已设计 (arch 3.9) |
| FR-105 | 系统应支持 Code Reviewer Subagent,自动化 code review 并写入 code_review.md | P1 | ✅ 已设计 (arch 3.14) |
| FR-106 | 系统应支持任务归档,完成的 task 文件夹自动移动到 tasks/archive/ | P1 | ✅ 已设计 (arch 3.15) |
| FR-107 | 系统应提供第三层规则示例模板(模块隔离/i18n/logger/接口保护等) | P1 | ✅ 已设计 (arch 3.16) |
| FR-108 | 系统应支持 YAML Frontmatter,三件套文件包含 task_id/status/version 等元数据 | P1 | ✅ 已设计 (arch 3.4 + 模板) |
| FR-109 | 系统应支持 Why-First Subagent,专门负责生成定向 Why 问题并查询 project-why.md | P1 | ✅ 已设计 (arch 3.1) |
| FR-110 | 系统应支持失败记录,所有 Linter/测试/revert 失败都追加到 project-why.md | P1 | ✅ 已设计 (arch 3.9.4 + 3.9.6) |
| FR-111 | 系统应支持 PR 自动生成,基于 plan.md + code_review.md 生成 PR 描述 | P1 | ✅ 已设计 (arch 3.6.6) |
| FR-112 | 系统应支持分支管理,任务创建时自动创建并切换分支,支持多任务切换 | P1 | ✅ 已设计 (arch 3.6.4) |
| FR-113 | 系统应支持自动分支管理,任务创建时自动创建并切换到新分支(feature/YYYY-MM-DD-<name>) | P1 | ✅ 已设计 (arch 3.6.4) |
| FR-114 | 系统应支持 SKILL Marketplace,主 SKILL 可调用子 SKILL(如 /nomos:update-why、/nomos:validate) | P1 | ✅ 已设计 (arch 11.1) |
| FR-115 | 系统应支持 /nomos:new-task 子命令,创建新任务并初始化文件夹 | P1 | ✅ 已设计 (arch 3.6.4) |
| FR-116 | 系统应支持任务上下文按需注入,只在明确需要时加载完整文档 | P1 | ✅ 已设计 (arch 3.4) |
| FR-117 | 系统应支持任务缓存,加速 /nomos:list-tasks 命令执行 | P1 | ✅ 已设计 (arch 3.17) |
| FR-118 | 系统应支持 Honest Questioning Engine,检测 Agent 是否真正理解用户批注 | P1 | ✅ 已设计 (arch 3.10.6) |
| FR-119 | 系统应支持 Knowledge Similarity Detector,检测 project-why.md 中的相似内容 | P1 | ✅ 已设计 (arch 3.12.1) |
| FR-120 | 系统应支持知识合并操作,将相似内容整合并与用户确认 | P1 | ✅ 已设计 (arch 3.12.2) |
| FR-121 | 系统应支持标注触发机制,通过手动命令"继续"/"处理标注"启动 Agent 处理 | P1 | ✅ 已设计 (arch 3.10.6) |
| FR-122 | 系统应支持标注状态流转: pending → pending_ai_question → pending_user_clarify → addressed | P1 | ✅ 已设计 (arch 2.5.3) |
| FR-123 | 系统应支持源码行号兜底,所有标注记录 source_line 防止行号漂移 | P1 | ✅ 已设计 (arch 2.5.4) |
| FR-124 | 系统应支持 WebSocket + 轮询混合刷新,确保内容动态更新 | P1 | ✅ 已设计 (arch 2.5.5) |
| FR-125 | 系统应支持 commit 粒度检查,在 Stop Hook 中验证 commit 数量与 Gate 数量匹配 | P1 | ✅ 已设计 (arch 3.6.3) |
| FR-126 | 系统应支持分支命名规范: {type}/{date}-{task-name} 格式 | P1 | ✅ 已设计 (arch 3.6.4) |
| FR-127 | 系统应支持 PR 手动触发,通过 /nomos:pr 命令创建 | P1 | ✅ 已设计 (arch 3.6.6) |
| FR-128 | 系统应支持 /nomos:clarify 子命令,提供轻量级需求澄清对话 | P1 | ✅ 已设计 (arch 3.6.7) |
| FR-129 | 系统应在 clarify 中借鉴 doc-architect 的结构化思维,提取关键词、痛点、约束 | P1 | ✅ 已设计 (arch 3.6.7) |
| FR-130 | 系统的 clarify 应不生成文件,只在控制台输出澄清报告供用户确认 | P1 | ✅ 已设计 (arch 3.6.7) |

### 5.3 Could Have Requirements

| ID | Requirement | Priority | 设计状态 |
|----|-------------|----------|----------|
| FR-201 | 系统应支持 YAML 配置文件,用户零代码配置第三层规则 | P2 | ✅ 已设计 (arch 3.18.1 → PRD Q1) |
| FR-202 | 系统应支持增量 Linter 检查,大型项目只检查变更部分 | P2 | ✅ 已设计 (arch 3.18.2 → PRD Q8) |
| FR-203 | 系统应支持 Linter 误报的人工覆盖机制 | P2 | ✅ 已设计 (arch 3.18.3 → PRD Q5) |
| FR-204 | 系统应支持跨文件依赖检查(如 trace_id 在调用链传递) | P2 | ✅ 已设计 (arch 3.18.4 → PRD Q6) |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Linter 检查延迟 | < 5 秒(Command Handler) | PreToolUse Hook 执行时间 |
| Prompt Handler 延迟 | < 8 秒(Haiku 单轮) | 语义判断响应时间 |
| Agent Handler 延迟 | < 60 秒(深度验证) | Subagent 完整执行时间 |
| Task 文件夹切换 | < 1 秒 | SessionStart Hook 加载时间 |
| 大型项目 Linter | < 10 秒(增量检查) | 只检查变更文件 |

### 6.2 Security

- 第二层规则必须覆盖 OWASP Top 10 安全漏洞(SQL 注入、XSS、硬编码密钥等)
- Hooks 脚本必须经过安全审查,避免命令注入风险
- plan.md 中的敏感信息(如 API key)必须标记为 [REDACTED]
- Subagent 只能使用只读工具(Read/Grep),禁止 Write/Edit
- Git revert 操作必须有确认机制,避免误删代码

### 6.3 Scalability

- 支持单个项目 100+ 个 task 文件夹
- 支持 10+ 种编程语言的 AST 解析(通过 Tree-sitter)
- 支持 50+ 条自定义第三层规则
- 支持 10+ 个 Subagent 并发执行
- 支持多任务分支切换开发

### 6.4 Compatibility

| Platform | Versions |
|----------|----------|
| Claude Code | >= 1.0 (2026 年 2 月版本) |
| Python | >= 3.8 |
| Node.js | >= 16 (可选,用于 Tree-sitter) |
| Git | >= 2.30 |
| 操作系统 | macOS / Linux / Windows (WSL) |

### 6.5 Maintainability

- BaseRule 接口必须保持向后兼容
- 所有 Hooks 脚本必须包含清晰的注释和错误处理
- 三件套模板必须包含 YAML Frontmatter 和 Review Comments 示例
- 第三层规则必须提供 10+ 个开箱即用的示例模板
- 文档必须包含完整的 Hooks 配置示例和故障排查指南

---

## 7. User Interface Requirements

### 7.1 Design Principles

- **文档优先**: 所有交互通过 Markdown 文件,而非 GUI
- **标注友好**: 通过 Task Viewer HTML 界面直接在 plan.md 里高亮标注
- **结构化输出**: Linter 报告必须是 JSON 格式,易于解析
- **可追溯性**: 所有批注和审查记录永久保存在 MD 文件里
- **最小干扰**: Hooks 在后台执行,不打断主 Agent 工作流

### 7.2 Key Screens

| Screen | Description | Key Elements |
|--------|-------------|--------------|
| research.md | 需求分析和现有代码调研 | Task Background, Existing Architecture, Protected Interfaces, Human Notes |
| plan.md | 方案计划和标注循环 | Goal, Phase Gates, Protected Interfaces, Review Comments, Change Log, Mermaid 图(文本形式) |
| code_review.md | 代码审查和修复记录 | Automated Checks, AI Reviewer Summary, Test Results, Review Comments |
| .claude/settings.json | Hooks 配置文件 | PreToolUse/PostToolUse/Stop Hook 配置,Command/Prompt/Agent Handler |
| .task-viewer.html | Task Viewer HTML 界面 | Markdown/Mermaid 渲染,标注功能,Python 后端通信 |

### 7.3 Task Viewer HTML 界面

**设计目标**: 提供独立于 IDE 的任务查看和标注界面,支持 Markdown/Mermaid 渲染和在线标注。

**技术架构**:
- **前端**: HTML + CSS + Pure JavaScript,无需构建工具
- **后端**: Python HTTP 服务器,提供文件读写和 WebSocket 通信
- **渲染**: CDN 引入 marked.js(Markdown)和 mermaid.js(图表)
- **位置**: tasks/t1-xxx/.task-viewer.html

**核心功能**:
1. **Markdown 渲染**: 实时渲染 plan.md 内容,支持代码高亮
2. **Mermaid 图表**: 自动渲染流程图、架构图、时序图
3. **在线标注**: 点击段落添加 Review Comments,格式与现有一致
4. **实时同步**: 标注自动保存到 plan.md,支持多端同步
5. **快捷操作**: 快捷键支持(Ctrl+S 保存,Ctrl+/ 添加标注)

**标注交互设计**:
1. **右键创建标注**: 右键点击文档行 → 高亮该行 → 打开新建标注框
2. **左键查看历史**: 左键点击标记点 → 打开标注历史面板 → 查看用户标注/Agent回复/AI追问
3. **AI 追问提示**: pending_ai_question 状态 → 紫色闪烁图标 → 提示用户澄清
4. **双视图切换**: [渲染]/[源码] 按钮 → 切换视图 → 特殊格式精确定位
5. **内容动态刷新**: Agent 修改后自动刷新 → 保留标注框状态 → 显示更新提示

**服务器特性**:
- **自动关闭**: 超时 30 分钟无活动自动关闭
- **浏览器通知**: 浏览器关闭时通过 WebSocket 通知服务器关闭
- **动态端口**: 从 8765 开始,自动检测并分配可用端口
- **多实例**: 支持同时打开多个任务查看器

**短 ID 映射系统**:
- **目录格式**: tasks/t1-YYYY-MM-DD-feature/
- **短 ID 可见**: 目录名包含短 ID(t1, t2, t3...),便于识别
- **模糊匹配**: 支持通过短 ID 或完整路径引用任务
- **自动分配**: 创建任务时自动分配下一个可用短 ID

**Git 集成特性**:
- **自动分支创建**: /nomos:start 时自动创建 feature/{date}-{name} 分支
- **Gate Commit**: 每个 Gate 完成后自动 commit,message 格式 <type>(<scope>): <desc> #gate-X.Y
- **PR 一键生成**: 任务完成后执行 /nomos:pr,自动生成 PR 描述

### 7.4 Mermaid 图可视化

**重要说明**: Claude Code CLI 是纯文本终端界面,无法直接渲染 Mermaid 图。Agent 生成的 Mermaid 代码以文本形式嵌入 plan.md 中。

**查看 Mermaid 图的方式**:

**Task Viewer HTML 界面** (唯一推荐方式):
- 使用内置的 Task Viewer 浏览器界面
- 自动渲染 Mermaid 图,无需额外配置
- 支持在线标注和实时同步
- 通过 `/nomos:view-task` 命令启动

### 7.5 Accessibility

- Markdown 文件必须符合 CommonMark 规范,确保跨工具兼容
- YAML Frontmatter 必须可被 jq / Python yaml 库解析
- Review Comments 格式必须支持 threaded 讨论(Thread + Addressed 标记)
- Hooks 错误消息必须清晰易懂,包含具体修复建议
- Mermaid 图必须使用标准语法,确保在各种渲染工具中正确显示
- Task Viewer HTML 界面必须支持键盘导航和屏幕阅读器

---

## 8. Data & Privacy

### 8.1 Data Collection

| Data Type | Purpose | Retention |
|-----------|---------|-----------|
| Task 文件夹内容 | 持久化任务状态,支持跨会话恢复 | 永久(直到手动归档) |
| Linter 报告 | 记录代码质量检查结果 | 保存在 code_review.md |
| Review Comments | 记录人类批注和 Agent 回复 | 保存在 plan.md |
| Hooks 执行日志 | 调试和故障排查 | 临时(/tmp/),会话结束后清理 |

### 8.2 Privacy Requirements

- 所有数据存储在本地文件系统,不上传到云端
- plan.md 中的敏感信息(API key/密码)必须标记为 [REDACTED]
- Git 提交前必须检查是否包含敏感信息
- tasks/ 目录建议加入 .gitignore,避免意外提交

---

## 9. Success Metrics

### 9.1 Key Performance Indicators

| Metric | Target | Timeline |
|--------|--------|----------|
| Agent 生成代码的 Linter 通过率 | > 95% | 3 个月内 |
| 人类批注后的计划修改次数 | < 3 次/任务 | 3 个月内 |
| 方向错误导致的 revert 次数 | < 10% 任务 | 6 个月内 |
| 代码 review 时间节省 | > 50% | 6 个月内 |
| Agent 编码速度提升 | > 2x | 6 个月内 |
| 生产环境 bug 减少 | > 30% | 12 个月内 |

### 9.2 Definition of Done

- [ ] BaseRule 接口和 AgentLinterEngine 核心引擎实现完成
- [ ] 第一层(语法)和第二层(安全)规则封装完成
- [ ] PreToolUse/PostToolUse/Stop Hook 配置模板完成
- [ ] Task 文件夹隔离和三件套模板完成
- [ ] Validator 和 Code Reviewer Subagent 实现完成
- [ ] 10+ 个第三层规则示例模板完成
- [ ] 完整文档(安装指南/配置示例/故障排查)完成
- [ ] 在 3+ 个真实项目中验证可用性

---

## 10. Assumptions & Constraints

### 10.1 Assumptions

- 用户已安装 Claude Code 并熟悉基本操作
- 用户项目已初始化 Git 仓库
- 用户熟悉 Markdown 和 YAML 语法
- 用户团队已有明确的代码规范和架构约束
- 用户愿意采用"文档优先"的工作方式

### 10.2 Constraints

- 必须绑定 Claude Code 生态,依赖 Hooks 机制
- Python ast 只支持 Python,多语言需 Tree-sitter
- Hooks 执行有超时限制(Command 5s, Prompt 8s, Agent 60s)
- YAML Frontmatter 必须存在,否则 Hooks 无法解析
- Git 操作(revert/commit)需要用户有相应权限

---

## 11. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Hooks 超时导致工作流卡住 | 高 | 中 | 优化 Linter 性能,支持增量检查,提供超时配置 |
| Linter 误报导致 Agent 无法写入代码 | 高 | 中 | 提供人工覆盖机制,支持临时禁用特定规则 |
| Task 文件夹管理混乱 | 中 | 中 | 提供自动归档机制,清晰的命名规范 |
| 第三层规则编写门槛高 | 中 | 高 | 提供 10+ 个示例模板,详细文档和教程 |
| Git revert 误删重要代码 | 高 | 低 | 添加确认机制,自动备份到 .old 分支 |
| 多语言支持不完善 | 中 | 中 | 优先支持主流语言(Python/JS/TS),逐步扩展 |
| 社区采用率低 | 高 | 中 | 开源到 GitHub,提供完整示例项目,积极推广 |

---

## 12. Open Questions

### Q1: 第三层规则的 YAML 配置格式如何设计？如何平衡灵活性和易用性？

**结论: 采用「声明式 YAML + 可选 Python 扩展」双轨模式。**

80% 的业务规则可以用声明式 YAML 覆盖（模式匹配 + 禁止/强制），剩余 20% 复杂场景走 Python BaseRule 扩展。

```yaml
# .claude/rules/layer3.yml
rules:
  - name: "force-decimal-for-money"
    description: "金融项目金额字段必须使用 Decimal"
    severity: error
    match:
      pattern: "float|double"
      context: "money|price|amount|balance"
    fix: "使用 Decimal 类型替代 float/double"

  - name: "require-tenant-id"
    description: "多租户项目查询必须带 tenant_id"
    severity: error
    match:
      ast_type: "function_call"
      function: "query|filter|select"
    require:
      argument: "tenant_id"
    fix: "在查询条件中添加 tenant_id 参数"

  - name: "custom-i18n"
    description: "使用 customT() 替代 t()"
    severity: error
    match:
      pattern: "\\bt\\("
      exclude: "customT\\("
    fix: "将 t() 替换为 customT()"

  # 复杂规则引用 Python 文件
  - name: "module-isolation"
    description: "模块隔离检查"
    severity: error
    handler: ".claude/rules/module_isolation.py"
```

**设计要点**:
- `match.pattern`: 正则匹配，覆盖简单文本模式
- `match.ast_type`: AST 节点匹配，覆盖结构化检查（需 Tree-sitter）
- `require`: 强制要求某些元素存在
- `handler`: 复杂逻辑委托给 Python 脚本
- 所有规则统一输出 JSON 格式，与 AgentLinterEngine 对接

**优先级**: P2（FR-201 已列入 Could Have），建议在核心流程稳定后实现。

---

### Q2: Hooks 如何动态切换 Task 文件夹？是否需要 .claude/current-task.txt 文件？

**结论: 已解决。current-task.txt 是必需的，且已纳入架构设计。**

当前架构已明确设计了完整的任务切换机制（参见 03_System_Architecture.md 3.4 节和 3.6.4 节）：

1. `.claude/current-task.txt` 记录当前活跃任务路径（如 `tasks/t1-2026-02-25-user-login`）
2. `SessionStart Hook` 读取该文件，显示轻量级提示
3. `UserPromptSubmit Hook` 检测任务切换意图（自然语言或 `/nomos:switch-task`）
4. 切换时自动 `git stash` → `git checkout` → 更新 `current-task.txt` → 加载新任务上下文

**此问题已关闭** ✅

---

### Q3: 多语言项目如何统一管理？是否需要语言级别的配置隔离？

**结论: 采用「语言自动检测 + 分语言规则集 + 统一引擎」模式，不需要语言级别的配置隔离。**

**方案设计**:

```yaml
# .claude/rules/languages.yml
language_config:
  python:
    layer1: ["ruff", "mypy"]
    layer2: ["bandit", "semgrep"]
    test_pattern: "test_*.py"
    formatter: "black"

  typescript:
    layer1: ["eslint", "tsc"]
    layer2: ["semgrep"]
    test_pattern: "*.test.ts"
    formatter: "prettier"

  go:
    layer1: ["golangci-lint"]
    layer2: ["gosec"]
    test_pattern: "*_test.go"
    formatter: "gofmt"

  # 通用规则（所有语言共享）
  shared:
    layer3: ".claude/rules/layer3.yml"  # 业务规则不分语言
```

**工作流程**:
1. `PreToolUse Hook` 从 `tool_input.file_path` 提取文件扩展名
2. 自动匹配对应语言的规则集
3. 第一二层走语言专属工具，第三层走统一 YAML 规则
4. 输出格式统一为 JSON，Agent 无感知差异

**不需要隔离的原因**: AgentLinterEngine 内部按语言分发即可，对外接口统一。Task 文件夹和 plan.md 是语言无关的。

**优先级**: P1（FR-101 Tree-sitter 多语言支持已列入 Should Have）。初期只支持 Python + TypeScript，后续按需扩展。

---

### Q4: 子 Agent 审查 checklist 如何标准化？是否需要可配置的审查模板？

**结论: 需要可配置的审查模板，采用「内置默认 + 项目覆盖」模式。**

**内置默认 Checklist**:

```yaml
# .claude/templates/validator-checklist.yml
validator:
  research_phase:
    - "是否识别了所有受影响的模块？"
    - "是否列出了 Protected Interfaces？"
    - "是否与 project-why.md 已有知识一致？"
    - "是否遗漏了边界条件？"

  plan_phase:
    - "Phase Gates 是否覆盖所有需求点？"
    - "是否有未定义的接口或数据结构？"
    - "Mermaid 图是否与文字描述一致？"
    - "是否考虑了错误处理和降级方案？"
    - "是否违反了 Protected Interfaces？"

# .claude/templates/reviewer-checklist.yml
reviewer:
  code_review:
    - "代码是否与 plan.md 的 Phase Gates 一一对应？"
    - "是否通过了所有三层 Linter 规则？"
    - "测试覆盖率是否达标？"
    - "是否有硬编码的配置值？"
    - "是否有未处理的错误路径？"
    - "日志和监控是否完善？"
```

**项目覆盖机制**: 用户可在项目根目录创建同名文件覆盖默认项，或通过 `extends` 追加：

```yaml
# 项目级覆盖
extends: "default"
validator:
  plan_phase:
    - "是否使用了 customT() 进行国际化？"
    - "是否所有查询都带了 tenant_id？"
```

**Subagent 使用方式**: Validator/Reviewer Subagent 启动时自动加载对应 checklist，逐项检查并在 Review Comments 中输出结果。

**优先级**: P1，与 Validator Subagent（FR-010）和 Code Reviewer Subagent（FR-105）同步实现。

---

### Q5: 如何处理 Linter 误报？是否需要"信任列表"机制？

**结论: 需要，采用「三级豁免」机制。**

| 豁免级别 | 作用范围 | 配置方式 | 示例 |
|---------|---------|---------|------|
| 行级豁免 | 单行代码 | 行内注释 | `# noqa: RF001` / `// eslint-disable-next-line` |
| 文件级豁免 | 整个文件 | 文件头注释 | `# nomos-ignore: RF001, RF002` |
| 规则级豁免 | 全局禁用某规则 | YAML 配置 | `.claude/rules/ignore.yml` |

**配置文件**:

```yaml
# .claude/rules/ignore.yml
ignore:
  # 全局豁免
  global:
    - rule: "no-eval"
      reason: "测试文件中需要使用 eval 进行动态测试"
      files: ["tests/**/*.py"]

    - rule: "require-tenant-id"
      reason: "系统级查询不需要 tenant_id"
      files: ["src/system/**/*.py"]

  # 临时豁免（有过期时间）
  temporary:
    - rule: "force-decimal-for-money"
      reason: "迁移期间暂时允许 float，计划在 Sprint 5 完成迁移"
      expires: "2026-04-01"
      files: ["src/legacy/**/*.py"]
```

**安全约束**:
- 第二层安全规则（SQL 注入、XSS 等）不允许行级豁免，只能通过 YAML 配置 + 明确 reason
- 临时豁免必须设置过期时间，过期后自动恢复检查
- 所有豁免操作记录到 project-why.md 的 Exceptions 节

**优先级**: P2（FR-203 已列入 Could Have）。初期可先支持行内注释豁免，后续扩展 YAML 配置。

---

### Q6: 跨文件依赖如何检查？是否需要专门的 Agent Handler？

**结论: 需要，但分两阶段实现。**

**阶段一（P1）: 基于 plan.md 的声明式检查**

在 plan.md 中声明跨文件依赖关系，Validator Subagent 在审查时验证：

```markdown
## Protected Interfaces
- `src/auth/token.py::generate_token()` - 不可修改签名
- `src/db/models.py::User` - 不可删除字段

## Cross-File Dependencies
- `trace_id`: 必须从 `src/middleware/trace.py` 传递到所有 `src/api/*.py`
- `tenant_id`: 必须从 `src/middleware/tenant.py` 注入到所有 `src/db/queries/*.py`
```

Validator Subagent 使用 Grep/Read 工具验证这些声明是否被遵守。

**阶段二（P2）: 基于 AST 的自动检测**

```yaml
# .claude/rules/cross-file.yml
cross_file_rules:
  - name: "trace-id-propagation"
    description: "trace_id 必须在调用链中传递"
    check_type: "agent"  # 需要 Agent Handler 深度分析
    entry_points: ["src/api/**/*.py"]
    required_param: "trace_id"
    propagation_depth: 3  # 检查 3 层调用深度

  - name: "interface-protection"
    description: "Protected Interfaces 签名不可变更"
    check_type: "command"  # 静态 diff 检查即可
    interfaces_file: "plan.md#protected-interfaces"
```

**为什么分阶段**: 跨文件 AST 分析需要 Tree-sitter 支持（FR-101），且 Agent Handler 有 60s 超时限制。阶段一用 Subagent 的只读工具链即可覆盖大部分场景，成本低、可靠性高。

**优先级**: 阶段一 P1（随 Validator Subagent 实现），阶段二 P2（FR-204 已列入 Could Have）。

---

### Q7: 归档策略如何自动化？是否需要定期清理机制？

**结论: 采用「事件驱动归档 + 可选定期清理」模式。**

**事件驱动归档（默认）**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      任务归档流程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  触发条件: 任务所有 Phase Gates ✅ + code_review.md 通过        │
│                                                                  │
│  Step 1: 更新 YAML Frontmatter                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ status: done → archived                                     │ │
│  │ archived_at: 2026-02-25T18:00:00                           │ │
│  │ pr_url: https://github.com/xxx/pull/42                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  Step 2: 移动文件夹                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ mv tasks/t1-2026-02-25-user-login/                         │ │
│  │    tasks/archive/t1-2026-02-25-user-login/                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  Step 3: 更新映射                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - 更新 short-id-mapping.json                                │ │
│  │ - 清空 current-task.txt                                     │ │
│  │ - 更新 task-cache.json                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**定期清理（可选）**:

```yaml
# .claude/config.yml
archive:
  auto_archive: true          # 任务完成后自动归档
  cleanup_after_days: 90      # 归档 90 天后可清理
  cleanup_action: "compress"  # compress | delete
  keep_plan_md: true          # 清理时保留 plan.md（知识价值）
```

**不建议自动删除的原因**: 归档的 task 文件夹包含完整的决策历史（Why-First 问答、标注循环、失败记录），对项目知识库有长期价值。建议压缩而非删除。

**优先级**: 事件驱动归档 P1（FR-106），定期清理 P2。

---

### Q8: 性能优化如何实现？大型项目是否需要分布式 Linter？

**结论: 不需要分布式 Linter。采用「增量检查 + 并行执行 + 缓存」三板斧即可。**

**性能优化策略**:

| 策略 | 实现方式 | 预期效果 |
|------|---------|---------|
| 增量检查 | 只检查 `git diff` 变更的文件 | 减少 80%+ 检查量 |
| 并行执行 | 三层规则并行运行（不互相依赖） | 延迟降低 50% |
| 结果缓存 | 文件 hash 未变则跳过检查 | 重复检查零开销 |
| 按需加载 | 只加载当前语言的规则集 | 减少初始化时间 |

**增量检查实现**:

```python
def get_changed_files():
    """只获取本次变更的文件"""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True, text=True
    )
    return result.stdout.strip().split('\n')

def should_check(file_path, cache):
    """基于文件 hash 判断是否需要检查"""
    current_hash = hashlib.md5(open(file_path).read().encode()).hexdigest()
    if cache.get(file_path) == current_hash:
        return False  # 文件未变，跳过
    cache[file_path] = current_hash
    return True
```

**为什么不需要分布式**: Claude Code 是单用户本地工具，PreToolUse Hook 每次只检查一个文件（Agent 调用 Write/Edit 时触发）。即使大型项目，单文件检查在 5s 内完成绰绰有余。分布式 Linter 是 CI/CD 场景的需求，不是本系统的职责。

**优先级**: 增量检查 P2（FR-202），缓存和并行 P2。初期单文件检查性能已满足需求。

---

## Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| Agent | AI 智能体,如 Claude/GPT 等 LLM 驱动的编码助手 |
| Linter | 代码检查工具,用于静态分析代码质量 |
| Hooks | Claude Code 生命周期钩子,在特定事件触发时执行脚本 |
| BaseRule | 标准规则接口,所有 Linter 规则必须实现 |
| AgentLinterEngine | 核心引擎,负责加载和执行规则流水线 |
| PreToolUse | 工具执行前钩子,用于拦截和验证 |
| PostToolUse | 工具执行后钩子,用于后处理和反馈 |
| Stop Hook | Agent 准备结束响应时的钩子,用于阶段门控 |
| Subagent | 子 Agent,专门负责特定任务(如 Validator/Reviewer) |
| current-task.txt | 状态文件,记录当前活跃任务路径,支持会话恢复 |
| SessionStart Hook | 会话开始时触发的钩子,用于轻量级任务提示 |
| UserPromptSubmit Hook | 用户提交 prompt 时触发的钩子,用于智能检测任务切换 |
| Task Context Injection | 按需注入任务上下文,避免盲目加载导致污染 |
| /nomos:switch-task | 显式任务切换子命令 |
| /nomos:list-tasks | 任务列表查询子命令 |
| /nomos:new-task | 新任务创建子命令 |
| Annotation Loop | 标注循环,在文档中直接批注而非聊天对话 |
| pending_ai_question | AI 追问状态,Agent 不理解时主动提问,紫色闪烁提示 |
| Block-Level Annotation | 块级标注,用于代码块/Mermaid/表格等特殊格式 |
| Gate Commit | Gate 完成后自动 commit,message 包含 #gate-X.Y 标记 |
| Dual View | 双视图,渲染视图和源码视图切换,解决特殊格式标注 |

### B. References

- [Claude Code 官方文档](https://code.claude.com/docs)
- [Claude Code Hooks 指南](https://code.claude.com/docs/en/hooks-guide)
- [planning-with-files 项目](https://github.com/OthmanAdi/planning-with-files)
- [claude-code-hooks-mastery 项目](https://github.com/disler/claude-code-hooks-mastery)
- [Plankton 项目](https://github.com/alexfazio/plankton)
- [Tree-sitter 官方文档](https://tree-sitter.github.io/tree-sitter/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [Bandit 安全扫描](https://bandit.readthedocs.io/)
- [Semgrep 静态分析](https://semgrep.dev/)
- [Mermaid 官方文档](https://mermaid.js.org/)
- [marked.js - Markdown 解析器](https://marked.js.org/)
| Honest Questioning | 诚实追问机制,Agent 遇到不理解时必须提问而非迎合 |
| Knowledge Similarity Detection | 知识相似检测,识别 project-why.md 中的重复或相似内容 |
| Knowledge Merge | 知识合并,将相似内容整合并与用户确认 |
| Knowledge Enhancement | 知识增强,深化已有理解,提升知识质量 |
| Annotation Loop | 标注循环,在文档中直接批注而非聊天对话 |
| Understanding Alignment | 理解对齐,确保人机之间真正达成共识 |
