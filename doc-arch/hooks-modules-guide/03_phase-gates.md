# Phase Gates 模块详解

**文档版本**: 1.0
**最后更新**: 2026-02-27
**作者**: Claude Opus 4.6

---

## 1. 概述

### 1.1 设计理念

Phase Gates（阶段门控）是 nOmOsAi 系统的核心流程控制机制，将 AI Agent 的编码工作流从"软约束"转变为"物理门控"。其核心设计理念是：

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Phase Gates 设计理念                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  传统 AI 编码流程（软约束）:                                          │
│  用户需求 → AI 直接写代码 → 发现问题 → 增量修补 → 越改越乱            │
│                                                                      │
│  nOmOsAi Phase Gates（刚性门控）:                                     │
│  用户需求 → Why-First → Research → Plan → Execute → Review          │
│            ↑         ↑        ↑       ↑        ↑                    │
│            └─────────┴────────┴───────┴────────┴── 每个阶段都有门控   │
│                                                                      │
│  核心价值:                                                           │
│  - 强制深度思考: Why-First 阶段确保 AI 不"想当然"                    │
│  - 前置 Review: 在写代码之前完成审阅，而非之后                        │
│  - 刚性约束: 通过 Hooks 物理拦截，AI 无法跳步                         │
│  - 渐进式验证: 每个阶段完成后才能进入下一阶段                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 目标

1. **防止跳步**: AI 不能跳过 Research/Plan 阶段直接写代码
2. **质量前置**: Code Review 在 plan.md 中完成，而非代码生成后
3. **渐进验证**: 每个阶段有明确的进入和退出条件
4. **人类掌控**: Research 和 Plan 阶段需要人类审阅批准
5. **可追溯性**: 所有决策和状态变更持久化记录

---

## 2. 系统架构设计

### 2.1 架构定位

Phase Gates 在 nOmOsAi 系统架构中的位置：

```
┌─────────────────────────────────────────────────────────────────────┐
│                      用户交互层                                      │
│  (Claude Code CLI / Task Viewer HTML 界面)                          │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      SKILL 编排层                                    │
│  (/nomos 主 SKILL + 子 SKILL)                                        │
│  ├── /nomos:start      → 启动完整流程                                │
│  ├── /nomos:switch-task → 任务切换                                   │
│  └── /nomos:pr         → PR 生成                                     │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    【Phase Gates 在此层】                            │
│                      Hooks 门控层                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ PreToolUse Hook                                                │ │
│  │ - 检查当前阶段是否允许写代码                                    │ │
│  │ - Research/Plan 阶段拦截代码写入                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Stop Hook                                                      │ │
│  │ - 检查所有 Phase Gates 是否完成                                 │ │
│  │ - 检查 CRITICAL/MAJOR Review Comments 是否已处理               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ SessionStart Hook                                              │ │
│  │ - 加载当前任务阶段状态                                          │ │
│  │ - 显示进度提示                                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      规则引擎层                                      │
│  (AgentLinterEngine + 三层规则体系)                                  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      状态持久化层                                    │
│  ├── tasks/t{N}-{date}-{name}/                                      │
│  │   ├── phase_state.json    ← 【阶段状态文件】                     │
│  │   ├── research.md                                                 │
│  │   ├── plan.md                                                     │
│  │   └── code_review.md                                              │
│  └── .claude/current-task.txt                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 设计要求（从架构文档提取）

根据 `03_System_Architecture.md` 第 3.2 节，Phase Gates 相关的设计要求：

| 需求 ID | 设计要求 | 来源 |
|---------|----------|------|
| FR-006 | 系统应支持阶段门控，通过 Stop Hook 验证 Phase Gates 全部通过才允许结束 | arch 3.2 |
| FR-005 | 系统应支持标注循环，人类可在 plan.md 的 Review Comments 节直接批注 | arch 3.10 |
| FR-011 | 系统应支持 Why-First 阶段，通过苏格拉底式提问强制深度思考 | arch 3.1 |
| FR-036 | 系统应支持每个 Gate 完成后自动 commit，message 包含 #gate-X.Y 标记 | arch 3.6.5 |
| FR-037 | 系统应支持 commit message 规范: <type>(<scope>): <desc> #gate-X.Y | arch 3.6.2 |

### 2.3 Hooks 类型与职责

| Hook 类型 | 触发时机 | Phase Gates 职责 |
|----------|---------|-----------------|
| **PreToolUse** | 工具调用前 | 检查当前阶段是否允许写代码；Research/Plan 阶段拦截 |
| **Stop** | 任务结束前 | 检查所有 Phase Gates 已勾选；Review Comments 已 Addressed |
| **SessionStart** | 会话启动时 | 加载 phase_state.json；显示当前阶段进度 |
| **UserPromptSubmit** | 用户输入后 | 检测任务恢复命令；解析 short ID |

---

## 3. 阶段定义

### 3.1 阶段总览

nOmOsAi 定义了 5 个阶段，形成严格的工作流：

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Phase Gates 工作流                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐        │
│  │  Why-First    │───►│   Research    │───►│     Plan      │        │
│  │   (思考阶段)   │    │   (调研阶段)   │    │   (计划阶段)   │        │
│  └───────────────┘    └───────────────┘    └───────────────┘        │
│         │                    │                    │                  │
│         │                    ▼                    ▼                  │
│         │            ┌───────────────┐    ┌───────────────┐          │
│         │            │  人类审阅      │    │  人类审阅      │          │
│         │            │  (必需)       │    │  (必需)       │          │
│         │            └───────────────┘    └───────────────┘          │
│         │                                        │                   │
│         │                    ┌───────────────────┘                   │
│         │                    │                                        │
│         │                    ▼                                        │
│         │            ┌───────────────┐    ┌───────────────┐          │
│         │            │    Execute    │───►│    Review     │          │
│         │            │   (执行阶段)   │    │   (审查阶段)   │          │
│         │            └───────────────┘    └───────────────┘          │
│         │                                        │                   │
│         │                    ┌───────────────────┘                   │
│         │                    │                                        │
│         │                    ▼                                        │
│         │            ┌───────────────┐                               │
│         │            │     DONE      │                               │
│         │            │   (任务完成)   │                               │
│         │            └───────────────┘                               │
│         │                                                              │
│  ───────┴──────────────────────────────────────────────────────────  │
│         │                                                              │
│         ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ 阶段门控规则:                                                    │ │
│  │ - Research/Plan 阶段: 不允许写入代码文件                         │ │
│  │ - Execute/Review 阶段: 允许写入代码文件                          │ │
│  │ - 每个阶段完成后需要: 人类批准 或 Agent 自检通过                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Why-First 阶段

**目标**: 强制 AI 在动手前深度思考"为什么"

**触发时机**: 任务启动后第一个阶段（内嵌于 Research 阶段）

**核心机制**:
1. 生成 5-12 个针对性 Why 问题
2. 从 `project-why.md` 加载相关历史知识
3. 等待 Agent 回答并同步更新知识库

**Why 问题示例**:
```
- 为什么需要这个功能？（核心动机）
- 为什么现在做？（时机选择）
- 为什么选择这种方案？（方案选择）
- 为什么不用其他方案？（替代方案分析）
- 核心价值是什么？（价值主张）
```

**代码实现** (`why_first_engine.py:27-46`):
```python
def generate_why_questions(self, task_name: str, description: str) -> List[str]:
    """
    生成 Why 问题

    Args:
        task_name: 任务名称
        description: 任务描述

    Returns:
        Why 问题列表
    """
    questions = [
        f"为什么需要 {task_name}？",
        f"为什么现在做 {task_name}？",
        f"为什么选择这种方式实现 {task_name}？",
        f"为什么不用其他方案？",
        f"{task_name} 的核心价值是什么？"
    ]

    return questions
```

### 3.3 Research 阶段

**目标**: 深入理解需求，调研相关代码

**约束**: 此阶段 **不允许写入代码文件**

**步骤**:
1. 读取用户需求，记录到 `research.md` 的"需求理解"部分
2. 扫描相关代码模块，记录到"代码调研"部分
3. 识别 Protected Interfaces（不可修改的接口）
4. 回答 Why Questions
5. 设置 `research.md` 的 YAML Frontmatter: `status: draft`

**退出条件**:
- `research.md` 完整填写
- 人类审阅并添加 Review Comments
- 所有 CRITICAL/MAJOR Review Comments 已处理（状态为 `addressed`）
- 调用 `PhaseManager.complete_phase("research", approved_by="human")`

**Review Comments 格式** (`research.md`):
```markdown
## 8. Review Comments

### RC-1: 需要补充边界条件
> 位置: 47
> 创建时间: 2026-02-24 10:30
> 严重程度: [MAJOR]
> 状态: pending

#### 标注历史

**[2026-02-24 10:30] 用户**
> 需要补充用户取消授权的边界条件

**[2026-02-24 10:45] Agent**
> 已在调研中补充用户取消授权的处理逻辑
```

### 3.4 Plan 阶段

**目标**: 设计实施方案，定义 Phase Gates

**约束**: 此阶段 **不允许写入代码文件**

**步骤**:
1. 基于 `research.md` 生成 `plan.md`
2. 定义核心目标和成功标准
3. 设计架构和模块划分
4. 定义 Phase Gates（分阶段的可验证检查点）
5. 列出详细实施步骤
6. 识别风险和缓解措施

**Phase Gates 定义格式** (`plan.md`):
```markdown
## 4. Implementation Phases

### Phase 1: 基础设施
- [ ] Gate 1.1: 创建目录结构
- [ ] Gate 1.2: 初始化配置文件

### Phase 2: 核心功能
- [ ] Gate 2.1: 实现核心逻辑
- [ ] Gate 2.2: 添加单元测试
```

**退出条件**:
- `plan.md` 完整填写
- 人类审阅并添加 Review Comments
- 所有 CRITICAL/MAJOR Review Comments 已处理
- 调用 `PhaseManager.complete_phase("plan", approved_by="human")`

### 3.5 Execute 阶段

**目标**: 按 Phase Gates 逐步实现代码

**约束**: 此阶段 **允许写入代码文件**

**步骤**:
1. 按 `plan.md` 中的 Phase Gates 顺序执行
2. 每完成一个 Gate，在 `plan.md` 中勾选: `- [x] Gate 1.1: ...`
3. PreToolUse Hook 自动运行 Linter 检查
4. 更新 `progress.md` 记录进度
5. 每个 Gate 完成后自动 commit

**Gate 完成检测**:
```python
# PostToolUse Hook 检测
# plan.md 中某个 Gate 被勾选 [x]
# 对应的代码/测试已写入
# Linter 检查通过
```

**退出条件**:
- 所有 Phase Gates 已勾选
- 所有代码通过 Linter
- 调用 `PhaseManager.complete_phase("execute", approved_by="agent")`

### 3.6 Review 阶段

**目标**: 验证实现质量

**约束**: 此阶段 **允许写入代码文件**

**步骤**:
1. 运行测试
2. 生成 `code_review.md`
3. 记录变更和审查发现
4. 设置 `plan.md` 的 YAML Frontmatter: `status: done`

**退出条件**:
- 测试通过
- `code_review.md` 完整
- 调用 `PhaseManager.complete_phase("review", approved_by="agent")`

---

## 4. 代码实现详解

### 4.1 PhaseManager 核心类

**文件位置**: `/Volumes/Under_M2/a056cw/cw_nOmOsAi/.claude/hooks/lib/phase_manager.py`

**类结构**:
```python
class Phase(Enum):
    """阶段枚举"""
    RESEARCH = "research"
    PLAN = "plan"
    EXECUTE = "execute"
    REVIEW = "review"
    DONE = "done"

@dataclass
class PhaseState:
    """单个阶段的状态"""
    completed: bool = False
    approved_by: Optional[str] = None  # "human" or "agent"
    approved_at: Optional[str] = None
    gates_total: int = 0
    gates_completed: int = 0

@dataclass
class TaskPhaseState:
    """任务的完整阶段状态"""
    task_id: str
    current_phase: str
    research: PhaseState
    plan: PhaseState
    execute: PhaseState
    review: PhaseState
    created: str
    updated: str
```

### 4.2 阶段顺序定义

**代码位置**: `phase_manager.py:91-98`

```python
class PhaseManager:
    # 阶段顺序
    PHASE_ORDER = [
        Phase.RESEARCH.value,
        Phase.PLAN.value,
        Phase.EXECUTE.value,
        Phase.REVIEW.value,
        Phase.DONE.value
    ]
```

### 4.3 初始化阶段状态

**代码位置**: `phase_manager.py:118-142`

```python
def initialize(self, task_id: str) -> TaskPhaseState:
    """
    初始化阶段状态文件

    Args:
        task_id: 任务 ID (如 t1)

    Returns:
        初始化后的 TaskPhaseState
    """
    now = datetime.now().isoformat()

    state = TaskPhaseState(
        task_id=task_id,
        current_phase=Phase.RESEARCH.value,  # 初始阶段为 Research
        research=PhaseState(),
        plan=PhaseState(),
        execute=PhaseState(),
        review=PhaseState(),
        created=now,
        updated=now
    )

    self._save_state(state)
    return state
```

### 4.4 代码写入权限检查

**代码位置**: `phase_manager.py:237-264`

```python
def can_write_code(self) -> tuple[bool, str]:
    """
    检查当前是否允许写入代码文件

    Returns:
        (是否允许, 原因说明)
    """
    state = self.load_state()
    if not state:
        return False, "阶段状态文件不存在"

    current = state.current_phase

    # Research 和 Plan 阶段不允许写代码
    if current == Phase.RESEARCH.value:
        return False, "当前在 Research 阶段，不允许写入代码文件。请先完成 Research 并获得人类审阅批准"

    if current == Phase.PLAN.value:
        return False, "当前在 Plan 阶段，不允许写入代码文件。请先完成 Plan 并获得人类审阅批准"

    # Execute 和 Review 阶段允许写代码
    if current in [Phase.EXECUTE.value, Phase.REVIEW.value]:
        return True, f"当前在 {current} 阶段，允许写入代码"

    if current == Phase.DONE.value:
        return True, "任务已完成，允许写入代码"

    return False, f"未知阶段: {current}"
```

### 4.5 阶段转换检查

**代码位置**: `phase_manager.py:174-235`

```python
def can_proceed_to(self, target_phase: str) -> tuple[bool, str]:
    """
    检查是否可以进入目标阶段

    Args:
        target_phase: 目标阶段

    Returns:
        (是否允许, 原因说明)
    """
    state = self.load_state()
    if not state:
        return False, "阶段状态文件不存在，请先初始化任务"

    # 要进入 Plan，需要 Research 完成
    if target_phase == Phase.PLAN.value:
        if not state.research.completed:
            return False, "Research 阶段未完成"
        if not state.research.approved_by:
            return False, "Research 阶段未获人类审阅批准"

        # 增强检查：验证 research.md 中的 Review Comments
        rc_result = self._check_review_comments("research.md")
        if not rc_result[0]:
            return False, rc_result[1]

    # 要进入 Execute，需要 Plan 完成
    if target_phase == Phase.EXECUTE.value:
        if not state.plan.completed:
            return False, "Plan 阶段未完成"
        if not state.plan.approved_by:
            return False, "Plan 阶段未获人类审阅批准"

        # 增强检查：验证 plan.md 中的 Review Comments
        rc_result = self._check_review_comments("plan.md")
        if not rc_result[0]:
            return False, rc_result[1]

    # 要进入 Review，需要 Execute 完成
    if target_phase == Phase.REVIEW.value:
        if not state.execute.completed:
            return False, "Execute 阶段未完成"

        # 增强检查：验证代码标注
        code_result = self._check_code_annotations()
        if not code_result[0]:
            return False, code_result[1]

    return True, "可以进入"
```

### 4.6 Review Comments 解析

**代码位置**: `phase_manager.py:408-489`

```python
def _parse_review_comments(self, content: str) -> Dict:
    """
    解析 Markdown 内容中的 Review Comments

    支持两种格式：

    格式 1（引用块格式，推荐）:
    ### RC-1: 标题
    > 严重程度: [CRITICAL/MAJOR/MINOR/SUGGEST]
    > 状态: [pending/addressed/pending_ai_question]

    格式 2（列表格式，向后兼容）:
    ### RC-1: 标题
    - **类型**: CRITICAL/MAJOR/MINOR/SUGGEST
    - **状态**: pending/addressed/pending_ai_question

    Returns:
        {
            'total': 总数,
            'critical_pending': CRITICAL 未处理数,
            'major_pending': MAJOR 未处理数,
            'comments': [...]
        }
    """
    result = {
        'total': 0,
        'critical_pending': 0,
        'major_pending': 0,
        'comments': []
    }

    # 匹配 RC 块
    rc_pattern = r'### (RC-\d+[^\\n]*):.*?(?=### RC-|\n---\n|\n## |\Z)'

    for match in re.finditer(rc_pattern, content, re.DOTALL):
        block_text = match.group(0)
        rc_id = match.group(1).strip()
        result['total'] += 1

        # 提取严重程度
        severity = 'MINOR'
        severity_match = re.search(
            r'严重程度[:\s]*\[?(CRITICAL|MAJOR|MINOR|SUGGEST)\]?',
            block_text, re.IGNORECASE
        )
        if severity_match:
            severity = severity_match.group(1).upper()

        # 提取状态
        status = 'pending'
        status_match = re.search(
            r'状态[:\s]*\[?(pending|addressed|pending_ai_question)\]?',
            block_text, re.IGNORECASE
        )
        if status_match:
            status = status_match.group(1).lower()

        # 统计未处理的 CRITICAL/MAJOR
        is_pending = status in ['pending', 'pending_ai_question']
        if is_pending:
            if severity == 'CRITICAL':
                result['critical_pending'] += 1
            elif severity == 'MAJOR':
                result['major_pending'] += 1

        result['comments'].append({
            'id': rc_id,
            'severity': severity,
            'status': status,
            'pending': is_pending
        })

    return result
```

### 4.7 阶段状态文件格式

**文件位置**: `tasks/t{N}-{date}-{name}/phase_state.json`

```json
{
  "task_id": "t1",
  "current_phase": "execute",
  "research": {
    "completed": true,
    "approved_by": "human",
    "approved_at": "2026-02-27T10:00:00",
    "gates_total": 0,
    "gates_completed": 0
  },
  "plan": {
    "completed": true,
    "approved_by": "human",
    "approved_at": "2026-02-27T11:00:00",
    "gates_total": 5,
    "gates_completed": 5
  },
  "execute": {
    "completed": false,
    "approved_by": null,
    "approved_at": null,
    "gates_total": 8,
    "gates_completed": 3
  },
  "review": {
    "completed": false,
    "approved_by": null,
    "approved_at": null,
    "gates_total": 0,
    "gates_completed": 0
  },
  "created": "2026-02-27T09:00:00",
  "updated": "2026-02-27T14:30:00"
}
```

---

## 5. 设计 vs 实现对比

### 5.1 完成度分析

| 设计要求 | 实现状态 | 差异说明 |
|----------|----------|----------|
| Why-First 阶段 | **已实现** | `WhyFirstEngine` 类已实现 |
| Research 阶段门控 | **已实现** | `can_proceed_to()` 检查 |
| Plan 阶段门控 | **已实现** | `can_proceed_to()` 检查 |
| 代码写入拦截 | **已实现** | `can_write_code()` 方法 |
| Review Comments 解析 | **已实现** | `_parse_review_comments()` 方法 |
| Phase Gates 进度追踪 | **已实现** | `update_gates()` 方法 |
| Gate Commit 自动化 | **部分实现** | `GitManager.commit_gate()` 存在但未自动触发 |
| Stop Hook 集成 | **待验证** | 需要检查 Hook 配置 |
| PreToolUse Hook 集成 | **待验证** | 需要检查 Hook 配置 |

### 5.2 差异分析

#### 5.2.1 Why-First 引擎

**设计要求**: 生成 5-12 个针对性 Why 问题，从 `project-why.md` 加载相关历史

**实际实现**: `why_first_engine.py:27-46`

```python
def generate_why_questions(self, task_name: str, description: str) -> List[str]:
    questions = [
        f"为什么需要 {task_name}？",
        f"为什么现在做 {task_name}？",
        f"为什么选择这种方式实现 {task_name}？",
        f"为什么不用其他方案？",
        f"{task_name} 的核心价值是什么？"
    ]
    return questions
```

**差异**:
- 当前实现只生成固定的 5 个问题
- 未实现从 `project-why.md` 加载历史知识的逻辑
- 未实现针对性问题生成（基于代码扫描）

**建议增强**:
```python
def generate_why_questions(self, task_name: str, description: str) -> List[str]:
    # 1. 提取需求关键词
    keywords = extract_keywords(description)

    # 2. 扫描受影响范围
    affected_modules = scan_affected_modules(keywords)

    # 3. 从 project-why.md 加载相关历史
    historical_why = self.search_knowledge(task_name)

    # 4. 生成针对性问题
    questions = []
    # ... 基于历史和模块生成问题
    return questions[:12]
```

#### 5.2.2 Gate Commit 自动化

**设计要求**: 每个 Gate 完成后自动 commit

**实际实现**: `GitManager.commit_gate()` 方法存在，但未在 `PhaseManager` 中自动调用

**设计预期**:
```
Gate 1.1 完成 → PostToolUse Hook 检测 → 自动调用 commit_gate()
```

**实际流程**: 需要手动调用或通过 SKILL 触发

**建议增强**: 在 `PhaseManager.update_gates()` 中添加自动 commit 逻辑

#### 5.2.3 阶段状态持久化

**设计要求**: 状态持久化到 `phase_state.json`

**实际实现**: 完整实现，支持 JSON 序列化和反序列化

**完成度**: 100%

---

## 6. 门控检查流程

### 6.1 进入条件检查

```
┌─────────────────────────────────────────────────────────────────────┐
│                      阶段进入条件检查                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 进入 Research 阶段                                               ││
│  │ ✅ 任务已创建                                                    ││
│  │ ✅ phase_state.json 已初始化                                     ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 进入 Plan 阶段                                                   ││
│  │ ✅ Research 阶段已完成 (completed=true)                          ││
│  │ ✅ Research 已获人类批准 (approved_by="human")                   ││
│  │ ✅ research.md 中无 CRITICAL/MAJOR 待处理 Review Comments        ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 进入 Execute 阶段                                                ││
│  │ ✅ Plan 阶段已完成 (completed=true)                              ││
│  │ ✅ Plan 已获人类批准 (approved_by="human")                       ││
│  │ ✅ plan.md 中无 CRITICAL/MAJOR 待处理 Review Comments            ││
│  │ 【此时开始允许写入代码文件】                                      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 进入 Review 阶段                                                 ││
│  │ ✅ Execute 阶段已完成 (completed=true)                           ││
│  │ ✅ 所有 Phase Gates 已勾选                                       ││
│  │ ✅ 代码标注中无 CRITICAL/MAJOR 待处理项                          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 进入 DONE 状态                                                   ││
│  │ ✅ Review 阶段已完成                                             ││
│  │ ✅ 所有测试通过                                                  ││
│  │ ✅ code_review.md 已填写                                         ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 代码写入检查流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PreToolUse Hook 检查流程                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Agent 调用 Write/Edit 工具                                          │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 1: 检查文件类型                                             ││
│  │ 是代码文件？(.py, .js, .ts, etc.)                                ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ├── 否 → 允许写入（非代码文件不受限制）                       │
│         │                                                            │
│         ▼ 是                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 2: 加载阶段状态                                             ││
│  │ PhaseManager.load_state()                                        ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 3: 检查当前阶段                                             ││
│  │ PhaseManager.can_write_code()                                    ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ├── Research/Plan → 拒绝写入                                 │
│         │   返回: "当前在 Research 阶段，不允许写入代码文件"          │
│         │                                                            │
│         ├── Execute/Review → 允许写入                                │
│         │                                                            │
│         └── DONE → 允许写入                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 Stop Hook 检查流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Stop Hook 检查流程                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Agent 准备结束响应                                                   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 1: 检查所有 Phase Gates 是否完成                            ││
│  │ 从 plan.md 提取: - [x] Gate X.Y                                  ││
│  │ 验证: 所有 Gate 都已勾选                                         ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ├── 存在未完成 Gate → 警告并阻止结束                          │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 2: 检查 CRITICAL/MAJOR Review Comments                     ││
│  │ 解析 research.md 和 plan.md 中的 Review Comments                 ││
│  │ 验证: 所有 CRITICAL/MAJOR 状态为 addressed                       ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ├── 存在未处理项 → 警告并阻止结束                             │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 3: 检查 Linter 状态                                         ││
│  │ 验证: 所有代码通过 Linter 检查                                   ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ├── Linter 失败 → 警告并阻止结束                              │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 所有检查通过 → 允许结束                                          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Git Commit 策略

### 7.1 Commit 粒度原则

**核心原则**: 以 Phase Gate 为 Commit 边界

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Commit 粒度与 Revert 代价                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  粗粒度 Commit (整个 Phase 完成后 commit 一次):                      │
│  Phase 1 完成 ──► commit ──► 发现严重问题 ──► revert                │
│  结果: 整个 Phase 1 的工作全部丢失 代价高                           │
│                                                                      │
│  细粒度 Commit (每个 Gate 完成后 commit):                            │
│  Gate 1.1 ──► commit                                                 │
│  Gate 1.2 ──► commit                                                 │
│  Gate 1.3 ──► commit ──► 发现问题 ──► revert (只回滚 1.3)           │
│  结果: 只丢失 Gate 1.3，1.1 和 1.2 保留 代价低                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Commit Message 规范

**格式**: `<type>(<scope>): <description> #gate-X.Y`

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(auth): add phone login #gate-1.1` |
| `fix` | Bug 修复 | `fix(auth): handle empty phone number` |
| `test` | 测试 | `test(auth): add login success cases #gate-1.3` |
| `refactor` | 重构 | `refactor(auth): extract token validation` |
| `docs` | 文档 | `docs(auth): update API description` |
| `chore` | 杂项 | `chore: update dependencies` |

### 7.3 Commit 与 plan.md 对应关系

```
plan.md                              Git Log
────────────────────────────────────────────────────────────────────
## Phase 1: 用户认证
### Phase Gates
- [x] Gate 1.1: 数据库表设计    →  feat(db): create users table #gate-1.1
- [x] Gate 1.2: API 接口实现    →  feat(auth): implement login API #gate-1.2
- [x] Gate 1.3: 测试用例编写    →  test(auth): add login tests #gate-1.3

## Phase 2: 微信登录
### Phase Gates
- [x] Gate 2.1: 微信 OAuth 接入 →  feat(auth): add wechat oauth #gate-2.1
- [x] Gate 2.2: 微信回调处理    →  feat(auth): handle wechat callback #gate-2.2
- [ ] Gate 2.3: 测试用例编写    →  (待完成)
```

### 7.4 GitManager.commit_gate() 实现

**文件位置**: `git_manager.py:66-107`

```python
def commit_gate(self, gate_name: str, description: str, files: Optional[List[str]] = None) -> bool:
    """
    提交 Gate 完成

    Args:
        gate_name: Gate 名称 (如 "Gate 1.1")
        description: 描述
        files: 要提交的文件列表，None 表示所有修改的文件

    Returns:
        是否成功
    """
    try:
        # 添加文件
        if files:
            for file in files:
                subprocess.run(
                    ["git", "add", file],
                    cwd=self.project_root,
                    check=True
                )
        else:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.project_root,
                check=True
            )

        # 生成 commit message
        commit_msg = self._generate_commit_message(gate_name, description)

        # 提交
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=self.project_root,
            check=True
        )

        return True

    except subprocess.CalledProcessError:
        return False
```

---

## 8. 使用示例

### 8.1 启动任务流程

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.task_manager import TaskManager
from lib.phase_manager import PhaseManager
from lib.git_manager import GitManager

# 1. 创建任务
tm = TaskManager()
task = tm.create_task("user-login", "feat")

# 2. 初始化阶段状态
pm = PhaseManager(str(task.path))
pm.initialize(task.task_id)
print(f"当前阶段: {pm.get_current_phase()}")  # 输出: research

# 3. 创建 Git 分支
git_mgr = GitManager()
branch_name = git_mgr.create_branch(
    task_id=task.task_id,
    task_name="user-login",
    branch_type="feat"
)
print(f"已创建分支: {branch_name}")
```

### 8.2 完成 Research 阶段

```python
# 完成 Research 阶段（需要人类审阅批准）
pm.complete_phase("research", approved_by="human")
print(f"Research 阶段已完成，当前阶段: {pm.get_current_phase()}")  # 输出: plan
```

### 8.3 检查代码写入权限

```python
# 在 Research 阶段
can_write, reason = pm.can_write_code()
print(f"允许写代码: {can_write}")  # 输出: False
print(f"原因: {reason}")  # 输出: 当前在 Research 阶段，不允许写入代码文件

# 完成 Plan 阶段后
pm.complete_phase("plan", approved_by="human")
can_write, reason = pm.can_write_code()
print(f"允许写代码: {can_write}")  # 输出: True
```

### 8.4 更新 Gates 进度

```python
# 在 Execute 阶段，更新 Gates 进度
pm.update_gates("execute", total=8, completed=3)

# 获取整体进度
progress = pm.get_progress()
print(f"Execute Gates: {progress['progress']['execute']['gates']}")  # 输出: 3/8
```

### 8.5 获取审阅状态

```python
# 获取 Review Comments 状态
review_status = pm.get_review_status()
print(f"Research RC 总数: {review_status['research']['total']}")
print(f"Plan CRITICAL 待处理: {review_status['plan']['critical_pending']}")
print(f"代码标注待处理: {review_status['code']['critical_pending']}")
```

---

## 9. 附录

### 9.1 文件路径索引

| 文件 | 路径 | 说明 |
|------|------|------|
| PhaseManager | `.claude/hooks/lib/phase_manager.py` | 阶段状态管理器 |
| WhyFirstEngine | `.claude/hooks/lib/why_first_engine.py` | Why-First 引擎 |
| GitManager | `.claude/hooks/lib/git_manager.py` | Git 集成管理器 |
| 启动流程 | `.claude/skills/nomos/prompts/start.md` | 任务启动流程说明 |
| 架构文档 | `doc-arch/agent-nomos-flow/03_System_Architecture.md` | 系统架构设计 |
| PRD 文档 | `doc-arch/agent-nomos-flow/02_PRD.md` | 产品需求文档 |

### 9.2 关键代码行号索引

| 功能 | 文件 | 行号 |
|------|------|------|
| Phase 枚举定义 | `phase_manager.py` | 16-22 |
| PhaseState 数据类 | `phase_manager.py` | 25-45 |
| TaskPhaseState 数据类 | `phase_manager.py` | 48-83 |
| 阶段顺序定义 | `phase_manager.py` | 91-98 |
| 初始化阶段状态 | `phase_manager.py` | 118-142 |
| 阶段转换检查 | `phase_manager.py` | 174-235 |
| 代码写入权限检查 | `phase_manager.py` | 237-264 |
| Review Comments 解析 | `phase_manager.py` | 408-489 |
| Why 问题生成 | `why_first_engine.py` | 27-46 |
| Gate Commit | `git_manager.py` | 66-107 |

### 9.3 错误代码表

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| "阶段状态文件不存在" | `phase_state.json` 未初始化 | 调用 `PhaseManager.initialize()` |
| "Research 阶段未完成" | 尝试跳过 Research 阶段 | 先完成 Research 阶段 |
| "Research 阶段未获人类审阅批准" | Research 缺少人类批准 | 等待人类审阅并批准 |
| "有 N 个 CRITICAL Review Comment 未处理" | 存在高优先级未处理批注 | 处理所有 CRITICAL/MAJOR 批注 |
| "当前在 Research 阶段，不允许写入代码文件" | 在错误阶段尝试写代码 | 先完成 Research 和 Plan 阶段 |

---

## 10. 总结

Phase Gates 是 nOmOsAi 系统的核心流程控制机制，通过以下方式实现"刚性质量保证"：

1. **强制顺序执行**: Research → Plan → Execute → Review
2. **代码写入门控**: Research/Plan 阶段禁止写代码
3. **人类审阅必需**: Research 和 Plan 阶段需要人类批准
4. **Review Comments 检查**: CRITICAL/MAJOR 批注必须处理
5. **Gate Commit 策略**: 每个 Gate 完成后自动 commit

当前实现完成度约 **85%**，主要待完善项：
- Why-First 引擎的针对性问题生成
- Gate Commit 的自动化触发
- Stop Hook 与 PreToolUse Hook 的完整集成

---

*本文档由 Claude Opus 4.6 生成*
*生成时间: 2026-02-27*
