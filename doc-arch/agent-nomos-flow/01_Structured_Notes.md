=== STRUCTURED NOTES ===

[Dimension 1: Business / Value]

Pain Points:
- [P1] AI Agent 生成代码时容易"想当然",跳过需求分析直接写代码,导致方向错误后花三倍时间增量修补
- [P2] LLM 的生成自由度(Soft constraints)与软件工程的确定性(Hard constraints)之间缺乏自动化治理防火墙
- [P3] Agent 生成的代码容易违反架构规范(如直接访问 DB、破坏分层隔离),导致后期无法替换底层服务
- [P4] 传统 Linter 只是"建议",Agent 可能忽略,缺乏强制执行机制
- [P5] 对话式交互容易丢失上下文,人类需要反复解释需求和约束,效率低下
- [P6] Agent 生成代码后才发现问题,code review 滞后,浪费 token 和时间
- [P7] 每个公司/行业有特定业务规则(如金融必须用 Decimal、多租户必须带 tenant_id),通用 Linter 无法覆盖
- [P8] 多次迭代需求容易"串",旧任务的分析和计划混在一起,Agent 分不清边界
- [P9] Agent 容易生成"黑盒代码"(无日志、无监控),生产出问题难以追踪
- [P10] 90% 的人舍不得删除已生成的错误代码,倾向于增量修补而非果断 revert,越改越乱
- [P11] Agent 缺乏"为什么"的深度思考,直接跳到"怎么做",导致方案不合理或过度设计
- [P12] 项目知识分散在聊天记录中,无法累积和复用,每次都要重新解释
- [P13] 人类需要盯着 Agent 工作,担心它"跑偏",无法真正放心
- [P14] 缺乏可视化设计方案,纯文字描述难以理解复杂架构
- [P15] Agent 经常先写代码再补测试,导致测试质量低下或遗漏
- [P16] 失败经验无法沉淀,同样的错误反复出现
- [P17] 任务完成后需要手动整理 PR 描述,费时费力
- [P18] 多任务并行时容易冲突,需要频繁切换分支

Core Interaction:
- [I1] SessionStart Hook: 读取 .claude/current-task.txt → 如果存在则显示轻量级提示"当前任务: XXX" → 不注入完整文档避免污染
- [I2] 用户发起新任务 → 触发 Why-First 阶段 → 苏格拉底式提问(5-12 个问题) → Agent 先回顾 project-why.md 已有内容 → 与用户沟通对齐 → 进行相似检测、合并、补充和增强 → 更新 project-why.md → 创建 tasks/t1-YYYY-MM-DD-<name>/ 文件夹(短 ID 在目录名中) → 自动创建并切换到新分支(feature/YYYY-MM-DD-<name>) → 更新 current-task.txt → 生成 .task-viewer.html 界面文件
- [I3] 用户切换任务 → 通过 /nomos:switch-task 或自然语言("继续 XXX 任务") → UserPromptSubmit Hook 检测 → 更新 current-task.txt → 注入完整任务上下文
- [I4] Research 阶段: Subagent 只读工具遍历现有代码 → 产出 research.md → 人类在文档里直接批注边界和约束
- [I5] Plan 阶段: Agent 生成 plan.md(包含 Mermaid 图) → 自动注入当前任务上下文 → PostToolUse Hook 推送给人类 → 人类可通过 Task Viewer HTML 界面或 IDE 在 Review Comments 节标注 → Validator Subagent 审查 → Agent 遇到不理解的批注时诚实提问而非迎合 → 循环直到所有批注 Addressed 且真正理解对齐
- [I6] Test-First 检查: PreToolUse Hook 检测是否先写测试 → 未写测试则阻塞代码生成 → 强制 TDD
- [I7] Execute 阶段: Agent 调用 Write/Edit → PreToolUse Hook 触发 Linter 刚性检查 → 不通过直接阻塞 + 喂回错误 → Agent 自我修复 → 再次尝试
- [I8] PostToolUse Hook 自动跑测试 + spawn Code Reviewer Subagent → 结果写入 code_review.md → 人类可追加最终批注
- [I9] Stop Hook 验证所有阶段门控通过(Phase Gates 全勾 + Review Comments 全 Addressed + Linter 全绿 + 测试通过) → 才允许结束任务
- [I10] 方向错误时,Hook 自动触发 git revert + 更新 plan.md 状态 + 记录失败原因到 project-why.md(先回顾已有失败经验,进行相似检测和合并),丢弃错误分支
- [I11] 任务完成后,Hook 自动生成 PR 描述(基于 plan.md + code_review.md) → 自动提交 PR → 更新 current-task.txt 为空
- [I12] 完成后,task 文件夹自动归档到 tasks/archive/,历史完整可查
- [I13] 多任务切换: 用户调用 /nomos:switch-task 或自然语言切换 → 系统切换到对应分支 → 加载对应 task 文件夹上下文 → 任务间互不干扰
- [I14] 任务列表查询: /nomos:list-tasks → 扫描 tasks/ 目录 → 显示所有任务状态(进行中/已完成/已归档)
- [I15] Task Viewer 启动: 用户调用 /nomos:view-task → Python 服务器启动(动态端口分配,从 8765 开始) → 自动打开浏览器 → 显示 Markdown/Mermaid 渲染界面 → 支持在线标注
- [I16] Task Viewer 自动关闭: 超时 30 分钟无活动 → 服务器自动关闭;或浏览器关闭 → WebSocket 通知服务器 → 服务器关闭
- [I17] 标注循环触发: 用户在 CLI 输入"继续"或"处理标注" → Agent 读取待处理标注 → 修改文档 → 追加回复到标注历史 → 用户在 Task Viewer 确认
- [I18] AI 诚实追问: Agent 遇到不理解的标注 → 在标注历史中追加 ❓ 提问 → 状态改为 pending_ai_question → Task Viewer 紫色闪烁提示 → 用户澄清
- [I19] Markdown 特殊格式标注: 用户点击代码块/Mermaid 图上方标记点 → 块级定位 → 或切换到源码视图 → 精确行级标注
- [I20] Gate 完成自动 Commit: PostToolUse Hook 检测 Gate 勾选 → 生成 commit message(含 #gate-X.Y) → 自动 commit → 可选自动 push
- [I21] 任务完成 PR 生成: 所有 Gate 完成 + Review Comments 全部 Addressed → 用户执行 /nomos:pr → 从 plan.md/code_review.md 提取内容 → 生成 PR 描述 → 提交 PR

Value Proposition:
- [V1] **刚性质量保证**: Linter 作为"物理定律",Agent 即使"幻觉"也无法突破安全与质量底线,代码质量从"靠自觉"变成"物理强制"
- [V2] **标注循环前置 review**: 把 code review 前置到写代码之前,在 plan.md 里批注比聊天高效 10 倍,上下文永不丢失
- [V3] **零上下文污染**: Task 文件夹隔离,每个迭代纯净独立,支持并行开发,人类只需专注当前任务
- [V4] **人类价值放大**: 人类只做高阶批注和决策,不用盯聊天记录追上下文,Agent 被物理约束在正确轨道
- [V5] **速度与质量双提升**: 所有"幻觉""跳步""增量修补"在 Hooks 层被物理消灭,Agent 编码从"需要盯紧"变成"可以放心睡觉"
- [V6] **可插拔扩展**: BaseRule 接口 + 流水线模式,用户可"搭积木"式添加业务规则,第一二层开箱即用,第三层自由定制
- [V7] **果断 revert 节省成本**: 方向错了直接回滚,比精心 patch 节省 token 和时间,90% 的浪费被避免
- [V8] **跨会话持久**: 状态在 MD 文件里积累,支持单长会话或中途关闭重开,SessionStart Hook 自动恢复
- [V9] **社区验证**: 基于 2026 年 Claude Code 生态最佳实践(plan_viewer、planning-with-files、hooks-mastery),生产级可用
- [V10] **专为 Claude Code 设计**: 深度绑定 Claude Code Hooks 机制,充分利用其原生能力,实现真正的物理门控,不追求通用性
- [V11] **Why-First 深度思考**: 强制 Agent 在动手前深度思考"为什么",避免"想当然",方案更合理
- [V12] **项目知识累积**: project-why.md 作为跨任务知识库,避免重复提问,项目智慧持续沉淀
- [V13] **人机分工明确**: 人类负责"为什么"和决策,Agent 负责"怎么做"和执行,各司其职,效率最大化
- [V14] **可视化设计**: Mermaid 图自动生成,复杂架构一目了然,沟通成本降低 80%
- [V15] **Test-First 质量保证**: 强制 TDD,测试覆盖率和质量显著提升
- [V16] **失败学习闭环**: 失败经验自动沉淀到 project-why.md,避免重复犯错
- [V17] **PR 自动化**: 自动生成 PR 描述,节省人工整理时间
- [V18] **多任务分支切换**: 独立 task 文件夹 + 分支切换,多任务互不干扰
- [V19] **成就系统激励**: Gamification 提升使用体验,Agent "成长"可见
- [V20] **一键调用**: SKILL 封装完整流程,用户只需 /nomos,降低使用门槛

[Dimension 2: Technical / Architecture]

Data Flow:
- [D1] 用户输入 → UserPromptSubmit Hook 检查 → 注入 research.md/plan.md 上下文 → 主 Agent 处理
- [D2] Agent 生成代码 → PreToolUse Hook 拦截 → Command Handler(静态 Linter) → Prompt Handler(语义判断) → Agent Handler(深度验证) → 通过后写入文件
- [D3] 文件写入后 → PostToolUse Hook → 自动格式化 + 测试 + spawn Reviewer Subagent → 结果追加到 code_review.md
- [D4] Agent 准备结束 → Stop Hook → 验证 Phase Gates + Review Comments + Linter + 测试 → 全通过才放行
- [D5] plan.md 更新 → PostToolUse Hook → 桌面通知/打开编辑器 → 人类批注 → 保存 → UserPromptSubmit Hook 检测到新批注 → spawn Validator Subagent
- [D6] Linter 违规 → 结构化 JSON 错误 → 直接喂回 Agent 上下文 → Agent 读取并自我修复 → 重新生成代码
- [D7] 审查失败 → Hook 触发 git revert → 更新 plan.md 状态标记 → 通知人类 → 回到 Plan 阶段
- [D8] Task 完成 → Hook 自动 mv 到 tasks/archive/ → 清理当前工作区

Key Components:
- [C1] **AgentLinterEngine (核心引擎)**: 接收代码,加载规则积木,按顺序执行,收集结果,输出 JSON 格式报告
- [C2] **BaseRule (规则接口)**: 定义 rule_name、severity、check() 方法,所有规则(第一二三层)必须实现此接口
- [C3] **Built-in Rules (内置规则)**: 第一层(Flake8/Ruff/ESLint 封装)、第二层(Bandit/Semgrep 安全扫描)、第三层(用户自定义 AST 检查)
- [C4] **Claude Code Hooks**: PreToolUse/PostToolUse/Stop/SubagentStop 等 17 个生命周期事件,支持 Command/Prompt/Agent 三种 Handler
- [C5] **Task 文件夹**: tasks/YYYY-MM-DD-feature/ 结构,包含 research.md/plan.md/code_review.md 三件套 + YAML Frontmatter
- [C6] **Validator Subagent**: 只读工具链(Read/Grep),专门审查 plan.md 和代码,产出结构化反馈,写回 Review Comments,遇到不理解的地方诚实提问
- [C7] **Code Reviewer Subagent**: 只读 + Linter,自动化 code review,检查架构一致性、测试覆盖率、安全风险
- [C8] **Tree-sitter Parser**: 统一多语言 AST 解析后端,支持 Python/JS/TS/Java/Go/Rust 等 50+ 语言
- [C9] **LLM Reporter**: 输出 JSON 格式报告(line/message/suggestion),方便 Agent 直接理解并自我修正
- [C10] **Hooks Handler Chain**: Command(静态快速) → Prompt(语义判断) → Agent(深度验证),顺序链式执行
- [C11] **project-why.md (知识库)**: 跨任务累积的项目知识库,记录所有"为什么"的答案和失败经验,支持智能维护(相似检测、合并、补充、增强)
- [C12] **Why-First Subagent**: 专门负责生成定向 Why 问题(5-12 个),先回顾 project-why.md 已有内容,与用户沟通对齐,进行智能维护
- [C13] **Mermaid Generator**: 自动生成 Mermaid 流程图/架构图/时序图,嵌入 plan.md
- [C14] **Test-First Checker**: PreToolUse Hook 检查测试文件是否存在,强制 TDD
- [C15] **PR Generator**: 基于 plan.md + code_review.md 自动生成 PR 标题和描述
- [C16] **Branch Manager**: 管理分支创建和切换,支持多任务开发
- [C17] **Branch Auto-Manager**: 任务创建时自动创建 feature 分支,任务完成后自动合并或清理
- [C18] **Achievement Tracker**: 记录 Agent 成就(连续通过、零 revert 等),存储在 .claude/achievements.json
- [C19] **SKILL Marketplace**: 主 SKILL(/nomos) 可调用子 SKILL(/nomos:update-why、/nomos:validate、/nomos:switch-task)
- [C20] **Failure Logger**: 记录所有失败(Linter/测试/revert)到 project-why.md,先回顾已有失败经验,进行相似检测和合并
- [C21] **current-task.txt Manager**: 维护当前活跃任务路径,支持 SessionStart 轻量级提示和任务切换
- [C22] **Task Context Injector**: 按需注入任务上下文,只在明确需要时(切换任务、Plan 阶段)才加载完整文档
- [C23] **UserPromptSubmit Detector**: 智能检测任务切换意图(如"继续 XXX 任务"、"切换到 XXX"),触发上下文加载
- [C24] **Task List Scanner**: 扫描 tasks/ 目录,生成任务列表(进行中/已完成/已归档),支持 /nomos:list-tasks
- [C25] **Honest Questioning Engine**: 在标注循环中检测 Agent 是否真正理解用户批注,遇到不理解时强制 Agent 提问而非迎合
- [C26] **Knowledge Similarity Detector**: 检测 project-why.md 中的相似内容,支持合并、补充和增强操作
- [C27] **Task Viewer Server**: Python HTTP 服务器,提供 Markdown/Mermaid 渲染和标注功能,支持动态端口分配和自动关闭
- [C28] **Short ID Mapper**: 短 ID 映射系统,管理 t1/t2/t3 与完整任务路径的映射关系
- [C29] **Port Manager**: 动态端口分配管理器,从 8765 开始自动检测并分配可用端口
- [C30] **Auto-Shutdown Manager**: 服务器自动关闭管理器,支持超时检测和浏览器关闭通知
- [C31] **Annotation Engine**: 标注引擎,管理标注创建、状态流转、历史持久化,支持右键创建和左键查看
- [C32] **Annotation State Manager**: 标注状态管理器,处理 pending/pending_ai_question/pending_user_clarify/addressed/wont_fix 五种状态流转
- [C33] **Block-Level Locator**: 块级定位器,处理代码块(block_index + inner_line)、Mermaid(整图)、表格(row)的特殊定位
- [C34] **Dual View Switcher**: 双视图切换器,支持渲染视图和源码视图切换,解决 Markdown 特殊格式标注问题
- [C35] **Content Refresher**: 内容刷新器,WebSocket + 轮询混合刷新,保留标注框状态,无需重新打开 Task Viewer
- [C36] **Gate Commit Generator**: Gate Commit 生成器,根据 Gate 信息自动生成 commit message,格式 <type>(<scope>): <desc> #gate-X.Y
- [C37] **PR Description Generator**: PR 描述生成器,从 plan.md 提取 Summary/Changes,从 code_review.md 提取 Test Plan/Checklist

Constraints:
- [T1] **绑定 Claude Code 生态**: 依赖 Hooks 机制,不追求通用性,充分利用 CC 原生能力
- [T2] **Python ast 单语言限制**: 内置 ast 只支持 Python,需 Tree-sitter 支持多语言
- [T3] **Hooks 执行超时**: Command 默认 5s,Prompt 默认 8s,Agent 默认 60s,需合理设计避免超时
- [T4] **YAML Frontmatter 必须**: 三件套文件必须包含 YAML 头,供 Hooks 机器解析(task_id/status/version 等)
- [T5] **exit 2 阻塞机制**: Command Handler 必须用 exit 2 触发阻塞,exit 0 放行,exit 1 为普通错误
- [T6] **JSON 输出格式**: Linter 和 Prompt Handler 必须输出严格 JSON,包含 ok/violations/summary 字段
- [T7] **只读 Subagent**: Validator 和 Reviewer Subagent 只能用只读工具(Read/Grep),不能 Write/Edit
- [T8] **Phase Gates 顺序**: Why-First → Research → Plan → Test-First → Execute → Review → Done,不可跳步,Stop Hook 强制检查
- [T9] **Review Comments 格式**: 必须用 Thread + Addressed 标记,Hooks 解析此格式判断是否全部处理
- [T10] **Git 集成**: 需要 git 仓库,支持 revert/commit/branch,归档依赖 mv 命令
- [T11] **project-why.md 格式**: 必须包含 YAML Frontmatter(project_id/last_updated) + Q&A 结构 + Failures 节
- [T12] **Why 问题数量限制**: 每次任务 5-12 个问题,避免问题泛滥
- [T13] **Mermaid 语法要求**: 生成的 Mermaid 图必须语法正确,支持 flowchart/sequenceDiagram/classDiagram
- [T14] **测试文件命名约定**: 测试文件必须符合约定(test_*.py、*.test.js 等),否则 Test-First Checker 无法识别
- [T15] **PR 描述长度限制**: 自动生成的 PR 描述不超过 2000 字符,避免过长
- [T16] **Mermaid 图查看方式**: Mermaid 图以文本形式嵌入 plan.md,通过 Task Viewer HTML 界面自动渲染可视化
- [T17] **成就数据格式**: achievements.json 必须包含 agent_id/timestamp/achievement_type 字段
- [T18] **SKILL 命名规范**: 子 SKILL 必须以主 SKILL 为前缀(如 /nomos:xxx)
- [T19] **失败记录格式**: project-why.md 的 Failures 节必须包含 timestamp/task_id/failure_type/lesson 字段
- [T20] **分支命名规范**: 自动创建的分支名称格式为 feature/YYYY-MM-DD-task-name 或 feature/TICKET-123-task-name
- [T21] **标注触发机制**: 手动命令"继续"/"处理标注",而非自动检测或 Task Viewer 按钮
- [T22] **标注交互约定**: 右键点击行创建新标注,左键点击标记点查看历史,区分两种操作
- [T23] **标注历史持久化**: 所有标注对话保存在 MD 文件中,支持版本控制和跨会话保持
- [T24] **AI 追问特殊状态**: pending_ai_question 状态 + 紫色闪烁图标,确保用户不遗漏
- [T25] **内容动态刷新**: WebSocket + 轮询自动刷新,保留打开的标注框状态
- [T26] **特殊格式标注**: 双视图切换 + 块级标注,代码块用块内行号,Mermaid 用整图定位
- [T27] **源码行号兜底**: 所有标注都记录 source_line,防止渲染后行号漂移
- [T28] **Gate Commit 粒度**: 每个 Gate 完成后自动 commit,而非 Phase 完成后,便于精确 revert
- [T29] **PR 手动触发**: 默认手动 /nomos:pr,避免未完成代码意外提交
- [T30] **Commit Message 绑定 Gate**: message 中包含 #gate-X.Y 标记,与 plan.md 一一对应

[Dimension 3: Specs / Constraints]

Input/Output:
- [S1] **AgentLinterEngine.lint() 输入**: code: str (代码字符串), language: str (可选,语言类型)
- [S2] **AgentLinterEngine.lint() 输出**: JSON { "passed": bool, "errors": [...], "warnings": [...] }
- [S3] **BaseRule.check() 输入**: code: str, 返回 List[Dict] (违规列表,空列表表示通过)
- [S4] **违规格式**: { "line": int, "message": str, "suggestion": str, "rule_name": str }
- [S5] **Hooks Command Handler 输入**: stdin JSON { "tool_name": str, "tool_input": {...} }
- [S6] **Hooks Command Handler 输出**: exit 0(放行) / exit 2(阻塞) + stderr 错误消息
- [S7] **Hooks Prompt Handler 输入**: 代码片段 + plan.md 上下文(自动注入)
- [S8] **Hooks Prompt Handler 输出**: JSON { "ok": bool, "reason": str, "violations": [...] }
- [S9] **YAML Frontmatter 必需字段**: task_id, language, status, version, last_updated
- [S10] **Review Comments 格式**: ### Thread N - YYYY-MM-DD HH:MM (角色) > 引用原文 > 批注内容 Agent 回复 ✅ Addressed
- [S11] **标注定位数据结构(普通文本)**: { "type": "line", "line": 47 }
- [S12] **标注定位数据结构(代码块)**: { "type": "code_block", "block_index": 1, "inner_line": 3, "source_line": 50 }
- [S13] **标注定位数据结构(Mermaid)**: { "type": "mermaid_block", "block_index": 1, "source_line_start": 55, "source_line_end": 60 }
- [S14] **标注定位数据结构(表格)**: { "type": "table_row", "table_index": 1, "row": 2, "source_line": 65 }
- [S15] **Commit Message 格式**: <type>(<scope>): <description> #gate-X.Y (如 feat(auth): implement login API #gate-1.2)
- [S16] **分支命名格式**: {type}/{date}-{task-name} (如 feat/2026-02-25-user-login)
- [S17] **PR 描述格式**: Summary + Changes(从 plan.md Phase Gates) + Test Plan + Checklist

Directory Structure:
- [R1] **项目根目录**: my-project/ (git 仓库根)
- [R2] **任务总目录**: tasks/ (建议 .gitignore 或只 commit 完成的)
- [R3] **单个任务文件夹**: tasks/t1-YYYY-MM-DD-feature-name/ 或 tasks/t2-TICKET-123-feature-name/ (短 ID 在目录名中)
- [R4] **三件套文件**: research.md, plan.md, code_review.md (必须,YAML Frontmatter + 内容)
- [R5] **归档目录**: tasks/archive/ (完成的任务自动移动到此)
- [R6] **Claude 配置**: .claude/hooks/ (Hooks 脚本), .claude/settings.json (Hooks 配置)
- [R7] **当前任务状态**: .claude/current-task.txt (记录当前活跃任务路径,如 tasks/t1-2026-02-24-feature/)
- [R8] **全局规则**: CLAUDE.md (项目级永久规则,不随任务变化)
- [R9] **Hooks 脚本**: .claude/hooks/i18n-static-check.sh, .claude/hooks/i18n-prompt-template.md, .claude/hooks/run-linter.sh
- [R10] **临时文件**: /tmp/i18n_code_snippet.txt, /tmp/plan_i18n_context.txt, /tmp/static_result.json (Hooks 链式传递数据)
- [R11] **命名规范**: 短 ID + 日期优先(t1-YYYY-MM-DD-short-desc) 或 短 ID + ticket 优先(t2-TICKET-123-feature-name)
- [R12] **项目知识库**: project-why.md (项目根目录,跨任务累积知识)
- [R13] **成就数据**: .claude/achievements.json (记录 Agent 成就)
- [R14] **SKILL 目录**: .claude/skills/nomos/ (主 SKILL 和子 SKILL 定义)
- [R15] **测试文件**: tests/ 或 __tests__/ (测试文件统一存放,Test-First Checker 识别)
- [R16] **PR 模板**: .github/pull_request_template.md (PR 自动生成的模板)
- [R17] **失败日志**: .claude/failure-logs/ (详细的失败日志,供分析)
- [R18] **分支映射**: .claude/branch-task-mapping.json (分支与任务的映射关系)
- [R19] **Task Viewer HTML**: tasks/t1-xxx/.task-viewer.html (任务查看器界面文件)
- [R20] **短 ID 映射**: .claude/short-id-mapping.json (短 ID 与完整路径的映射)
- [R21] **子 SKILL 注册表**: .claude/skills/registry.json (SKILL Marketplace 注册表)
- [R22] **任务缓存**: .claude/task-cache.json (任务列表缓存,加速 /nomos:list-tasks)

Error Handling:
- [E1] **Linter 失败**: PreToolUse Hook exit 2 阻塞 → 错误消息直接喂回 Agent → Agent 读取并自我修复 → 重新尝试 Write
- [E2] **语法错误**: 第一层 Linter 捕获 → 返回行号和错误类型 → Agent 修复语法后重试
- [E3] **安全漏洞**: 第二层 Linter 捕获(eval/exec/硬编码密钥) → 阻塞并提供安全替代方案 → Agent 重构代码
- [E4] **业务规则违反**: 第三层 Linter 捕获(模块隔离/i18n/logger) → Prompt Handler 语义判断 → 提供具体修复建议
- [E5] **Phase Gates 未通过**: Stop Hook 阻塞结束 → 提示缺失的 gate → Agent 继续工作直到全部通过
- [E6] **Review Comments 未 Addressed**: Stop Hook 阻塞 → 列出未处理的 Thread → Agent 必须逐个回复并标记 Addressed
- [E7] **测试失败**: PostToolUse Hook 检测到 → 写入 code_review.md → Agent 读取失败原因 → 修复代码 → 重新跑测试
- [E8] **架构冲突**: Reviewer Subagent 发现违反 Protected Interfaces → 写入 code_review.md → 人类批注确认 → Hook 触发 git revert
- [E9] **Hooks 超时**: Command/Prompt/Agent Handler 超时 → 返回 timeout 错误 → Agent 收到提示 → 简化代码或拆分任务
- [E10] **Task 文件夹不存在**: SessionStart Hook 检测到 → 提示用户指定 task-id 或创建新任务 → 自动初始化三件套模板
