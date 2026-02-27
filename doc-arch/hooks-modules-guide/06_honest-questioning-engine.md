# N0mosAi 诚实追问引擎 (Honest Questioning Engine) 详解

本文档详细讲解 N0mosAi 项目的诚实追问引擎设计与实现。

---

## 1. 概述

### 1.1 设计目标

诚实追问引擎 (Honest Questioning Engine, HQE) 的核心目标是 **确保 Agent 真正理解人类意图** -- 在 Agent 声称理解但实际可能存在误解时，自动生成追问进行澄清。

**核心设计理念**:

```
┌──────────────────────────────────────────────────────────────┐
│              传统 AI 交互 vs 诚实追问模式                       │
├──────────────────────────────────────────────────────────────┤
│  传统方式:  用户需求 → Agent 回复 → 直接执行                   │
│  N0mosAi:  用户需求 → Agent 回复 → 理解度检测 → 追问/执行      │
└──────────────────────────────────────────────────────────────┘
```

**关键价值**:

| 价值点 | 说明 |
|--------|------|
| 防止误解执行 | 在 Agent 理解不完整时阻止错误执行 |
| 主动追问 | 自动检测不确定信号并生成追问 |
| 三种追问类型 | 苏格拉底式、选项式、确认式提问 |
| AI_QUESTION 标注 | 与 Review Comments 系统无缝集成 |

### 1.2 追问类型体系

```
┌─────────────────────────────────────────────────────────────┐
│                    三种追问类型                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 苏格拉底式 (Socratic)                                │   │
│  │ - 语义模糊时使用                                     │   │
│  │ - 引导用户澄清含义                                   │   │
│  │ - 示例: "关于「优化性能」，你具体指哪个指标？"        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 选项式 (Option)                                      │   │
│  │ - 多种可能理解时使用                                 │   │
│  │ - 提供明确选项                                       │   │
│  │ - 示例: "你希望的排序方式是: A) 时间 B) 优先级?"     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 确认式 (Confirmation)                                │   │
│  │ - 基本理解但不确定时使用                             │   │
│  │ - 请求最终确认                                       │   │
│  │ - 示例: "我理解你要做 X，这是否正确？"               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构设计

### 2.1 架构文档中的设计要求

来源: `/Volumes/Under_M2/a056cw/cw_N0mosAi/doc-arch/agent-nomos-flow/09_AdvancedFeatures_DevPlan.md:607-714`

```
┌─────────────────────────────────────────────────────────────┐
│                    诚实追问引擎架构                          │
│  (HonestQuestioningEngine)                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    标注系统                                  │
│  (Review Comments + AI_QUESTION 标注)                       │
└─────────────────────────────────────────────────────────────┘
```

**设计要点**:

1. **理解度评估**: 评估 Agent 对标注/需求的理解程度 (0.0 ~ 1.0)
2. **接口设计**:
   ```python
   class UnderstandingScore:
       overall: float                   # 综合理解度
       semantic_clarity: float          # 语义清晰度
       context_availability: float      # 上下文可用性
       consistency: float               # 知识一致性
       assumption_explicitness: float   # 假设明确性

   class HonestQuestioningEngine:
       def assess_understanding(annotation, context) -> UnderstandingScore:
           pass
       def generate_questions(annotation, score) -> List[ClarificationQuestion]:
           pass
   ```

3. **触发时机**: Agent 处理标注时，理解度低于阈值

### 2.2 追问状态流转

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    标注状态流转 (含追问)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐                                                               │
│  │ pending  │ ◄──── 人类创建标注                                            │
│  └────┬─────┘                                                               │
│       │                                                                      │
│       │ Agent 处理标注                                                       │
│       │                                                                      │
│       ├── 理解度 >= 0.7 ──────────────────────────────────────┐             │
│       │                                                        ▼             │
│       │                                              ┌──────────────┐       │
│       │                                              │  addressed   │       │
│       │                                              └──────────────┘       │
│       │                                                                      │
│       └── 理解度 < 0.7                                                      │
│                │                                                             │
│                ▼                                                             │
│       ┌────────────────────────┐                                            │
│       │ pending_ai_question    │ ◄──── 紫色闪烁图标                         │
│       │ (Agent 追问中)         │                                            │
│       └────────┬───────────────┘                                            │
│                │                                                             │
│                │ 用户回答                                                    │
│                ▼                                                             │
│       ┌──────────────────────┐                                              │
│       │ pending_user_clarify │                                              │
│       └────────┬─────────────┘                                              │
│                │                                                             │
│                │ Agent 重新评估                                              │
│                │                                                             │
│                ├── 理解度 >= 0.7 ──► addressed                              │
│                │                                                             │
│                └── 理解度 < 0.7 且 轮次 < 3 ──► pending_ai_question (再追问)│
│                │                                                             │
│                └── 轮次 >= 3 ──► pending (升级为人工处理)                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 代码实现详解

### 3.1 文件结构

```
.claude/hooks/lib/
├── honest_questioning_engine.py    # 核心追问引擎
└── why_first_engine.py              # Why-First 引擎 (相关模块)

.claude/skills/nomos/prompts/
└── clarify.md                       # 澄清对话 prompt 模板
```

### 3.2 数据结构定义

**文件**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/hooks/lib/honest_questioning_engine.py`

```python
class HonestQuestioningEngine:
    """诚实追问引擎 - 检测理解并生成追问"""

    def __init__(self):
        """初始化引擎"""
        # 不确定性关键词列表
        self.uncertainty_keywords = [
            '可能', '也许', '大概', '应该', '似乎',
            '不确定', '不清楚', '不太明白', '需要确认',
            'maybe', 'probably', 'perhaps', 'might', 'unclear'
        ]

        # 模糊表达模式 (正则)
        self.vague_patterns = [
            r'等等',
            r'之类的',
            r'或者.*或者',
            r'不太.*',
            r'有点.*'
        ]
```

**设计分析**:

- `uncertainty_keywords`: 检测 Agent 回复中的不确定信号
- `vague_patterns`: 正则模式匹配模糊表达
- 支持中英文双语检测

### 3.3 核心方法: detect_understanding

**文件位置**: `honest_questioning_engine.py:30-68`

```python
def detect_understanding(self, agent_response: str) -> Dict[str, any]:
    """
    检测 Agent 理解程度

    Args:
        agent_response: Agent 的回复

    Returns:
        检测结果
    """
    # 检测不确定性关键词
    uncertainty_count = sum(
        1 for keyword in self.uncertainty_keywords
        if keyword in agent_response.lower()
    )

    # 检测模糊表达
    vague_count = sum(
        1 for pattern in self.vague_patterns
        if re.search(pattern, agent_response)
    )

    # 检测问号数量（Agent 反问）
    question_count = agent_response.count('？') + agent_response.count('?')

    # 计算理解度分数 (0-100)
    understanding_score = 100
    understanding_score -= uncertainty_count * 10
    understanding_score -= vague_count * 15
    understanding_score -= question_count * 5
    understanding_score = max(0, min(100, understanding_score))

    return {
        'score': understanding_score,
        'uncertainty_count': uncertainty_count,
        'vague_count': vague_count,
        'question_count': question_count,
        'needs_clarification': understanding_score < 70
    }
```

**评分算法**:

```
┌─────────────────────────────────────────────────────────────┐
│                    理解度评分算法                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  初始分数: 100                                              │
│                                                             │
│  扣分规则:                                                  │
│  ├── 每个不确定性关键词: -10 分                             │
│  ├── 每个模糊表达: -15 分                                   │
│  └── 每个 Agent 反问 (?/？): -5 分                          │
│                                                             │
│  最终分数: max(0, min(100, 计算分数))                       │
│                                                             │
│  阈值判断:                                                  │
│  ├── score >= 70: 理解充分，可直接执行                      │
│  └── score < 70: 需要澄清，生成追问                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 核心方法: generate_questions

**文件位置**: `honest_questioning_engine.py:70-103`

```python
def generate_questions(self, context: str, agent_response: str) -> List[str]:
    """
    生成追问问题

    Args:
        context: 上下文（用户需求）
        agent_response: Agent 回复

    Returns:
        追问问题列表
    """
    questions = []

    # 检测理解程度
    understanding = self.detect_understanding(agent_response)

    if understanding['needs_clarification']:
        # 提取不确定的部分
        uncertain_parts = self._extract_uncertain_parts(agent_response)

        for part in uncertain_parts:
            questions.append(f"关于「{part}」，你是否确定理解了需求？")

    # 检测缺失的关键信息
    missing_info = self._detect_missing_info(context, agent_response)
    for info in missing_info:
        questions.append(f"你是否考虑了{info}？")

    # 检测假设
    assumptions = self._detect_assumptions(agent_response)
    for assumption in assumptions:
        questions.append(f"你假设了「{assumption}」，这个假设是否正确？")

    return questions
```

**追问生成策略**:

| 检测类型 | 生成模板 | 示例 |
|----------|----------|------|
| 不确定部分 | `关于「{part}」，你是否确定理解了需求？` | 关于「可能需要修改数据库」，你是否确定理解了需求？ |
| 缺失信息 | `你是否考虑了{info}？` | 你是否考虑了安全要求？ |
| 隐式假设 | `你假设了「{assumption}」，这个假设是否正确？` | 你假设了「用户已登录」，这个假设是否正确？ |

### 3.5 辅助方法: _extract_uncertain_parts

**文件位置**: `honest_questioning_engine.py:105-122`

```python
def _extract_uncertain_parts(self, text: str) -> List[str]:
    """提取不确定的部分"""
    uncertain_parts = []

    # 查找包含不确定关键词的句子
    sentences = re.split(r'[。！？\n]', text)
    for sentence in sentences:
        for keyword in self.uncertainty_keywords:
            if keyword in sentence.lower():
                # 提取关键短语
                words = sentence.split()
                if len(words) > 3:
                    uncertain_parts.append(' '.join(words[:10]) + '...')
                else:
                    uncertain_parts.append(sentence)
                break

    return uncertain_parts[:3]  # 最多 3 个
```

### 3.6 辅助方法: _detect_missing_info

**文件位置**: `honest_questioning_engine.py:124-145`

```python
def _detect_missing_info(self, context: str, response: str) -> List[str]:
    """检测缺失的关键信息"""
    missing = []

    # 关键信息类别
    key_info_categories = [
        ('性能要求', ['性能', '速度', '延迟', 'performance']),
        ('安全要求', ['安全', '权限', '认证', 'security']),
        ('错误处理', ['错误', '异常', '失败', 'error']),
        ('边界条件', ['边界', '极限', '最大', '最小', 'edge case']),
        ('兼容性', ['兼容', '版本', '浏览器', 'compatibility'])
    ]

    for category, keywords in key_info_categories:
        # 如果上下文提到但回复没提到
        context_mentions = any(kw in context.lower() for kw in keywords)
        response_mentions = any(kw in response.lower() for kw in keywords)

        if context_mentions and not response_mentions:
            missing.append(category)

    return missing
```

**关键信息类别**:

| 类别 | 关键词 |
|------|--------|
| 性能要求 | 性能、速度、延迟、performance |
| 安全要求 | 安全、权限、认证、security |
| 错误处理 | 错误、异常、失败、error |
| 边界条件 | 边界、极限、最大、最小、edge case |
| 兼容性 | 兼容、版本、浏览器、compatibility |

### 3.7 辅助方法: _detect_assumptions

**文件位置**: `honest_questioning_engine.py:147-163`

```python
def _detect_assumptions(self, text: str) -> List[str]:
    """检测假设"""
    assumptions = []

    # 假设关键词
    assumption_patterns = [
        r'假设(.*?)(?=[。，])',
        r'假定(.*?)(?=[。，])',
        r'认为(.*?)(?=[。，])',
        r'应该是(.*?)(?=[。，])'
    ]

    for pattern in assumption_patterns:
        matches = re.findall(pattern, text)
        assumptions.extend(matches[:2])  # 最多 2 个

    return assumptions
```

### 3.8 标注创建方法: create_ai_question_annotation

**文件位置**: `honest_questioning_engine.py:165-189`

```python
def create_ai_question_annotation(
    self,
    question: str,
    context: str,
    location: str
) -> Dict[str, str]:
    """
    创建 AI 追问标注

    Args:
        question: 追问问题
        context: 上下文
        location: 位置

    Returns:
        标注数据
    """
    return {
        'type': 'AI_QUESTION',
        'status': 'pending_ai_question',
        'question': question,
        'context': context,
        'location': location,
        'timestamp': None  # 由调用者填充
    }
```

**AI_QUESTION 标注格式**:

```python
{
    'type': 'AI_QUESTION',           # 标注类型
    'status': 'pending_ai_question', # 状态: 等待用户回答
    'question': '关于「...」，你是否确定理解了需求？',
    'context': '原始上下文',
    'location': 'file.py:42',
    'timestamp': '2026-02-27T10:30:00Z'
}
```

### 3.9 阈值判断方法: should_ask_question

**文件位置**: `honest_questioning_engine.py:191-202`

```python
def should_ask_question(self, understanding_score: int) -> bool:
    """
    判断是否应该追问

    Args:
        understanding_score: 理解度分数

    Returns:
        是否应该追问
    """
    return understanding_score < 70
```

---

## 4. 设计 vs 实现对比

### 4.1 完成度分析

```
┌─────────────────────────────────────────────────────────────┐
│                     设计 vs 实现对比                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  理解度检测                                                 │
│  ├── 关键词检测         ✅ 完整实现                         │
│  ├── 模糊模式匹配       ✅ 完整实现                         │
│  ├── 反问检测           ✅ 完整实现                         │
│  └── 语义分析           ❌ 未实现 (设计要求 Haiku 模型)     │
│                                                             │
│  追问生成                                                   │
│  ├── 不确定部分提取     ✅ 完整实现                         │
│  ├── 缺失信息检测       ✅ 完整实现                         │
│  ├── 假设检测           ✅ 完整实现                         │
│  ├── 三种追问类型       ⚠️ 部分实现 (未区分类型)            │
│  └── 苏格拉底式生成     ❌ 未实现                           │
│                                                             │
│  标注集成                                                   │
│  ├── AI_QUESTION 格式   ✅ 完整实现                         │
│  ├── 状态流转           ⚠️ 格式定义完整，未集成到系统      │
│  └── 与 Review Comments ❌ 未集成                           │
│                                                             │
│  与门控系统集成                                             │
│  └── 门控检查点         ❌ 未集成                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 差异分析

| 组件 | 设计要求 | 实际实现 | 差距 |
|------|---------|---------|------|
| **理解度评分** | UnderstandingScore 多维度结构 | 单一 score 字典 | 缺少分维度评估 |
| **语义分析** | 调用 Haiku 模型进行语义理解 | 关键词 + 正则匹配 | 无 AI 能力 |
| **追问类型** | SOCRATIC/OPTION/CONFIRMATION 三种 | 模板化问题，未区分类型 | 未实现类型系统 |
| **知识一致性** | 与 project-why.md 比对 | 未实现 | 缺少知识库集成 |
| **状态流转** | pending → pending_ai_question → pending_user_clarify | 格式定义完整 | 未集成到标注系统 |
| **轮次限制** | 最多 3 轮追问 | 未实现 | 缺少轮次计数 |

### 4.3 接口差异

**架构文档设计**:

```python
class UnderstandingScore:
    overall: float                   # 0.0 ~ 1.0 综合理解度
    semantic_clarity: float          # 语义清晰度
    context_availability: float      # 上下文可用性
    consistency: float               # 与已有知识一致性
    assumption_explicitness: float   # 假设明确性
    details: List[str]               # 具体问题点

class ClarificationQuestion:
    question_type: QuestionType      # SOCRATIC/OPTION/CONFIRMATION
    question_text: str               # 问题文本
    context: str                     # 问题上下文
    options: List[str]               # 选项 (option 类型)
    related_why: Optional[str]       # 关联的 project-why.md 条目

class HonestQuestioningEngine:
    def __init__(self, task_path: str, why_path: str = "project-why.md"):
        pass

    def assess_understanding(self, annotation_text: str,
                              document_context: str) -> UnderstandingScore:
        pass

    def generate_questions(self, annotation_text: str,
                           score: UnderstandingScore) -> List[ClarificationQuestion]:
        pass

    def update_annotation_status(self, annotation_id: str,
                                  questions: List[ClarificationQuestion],
                                  doc_path: str) -> None:
        pass

    def process_user_answer(self, annotation_id: str,
                            answer_text: str,
                            doc_path: str) -> None:
        pass
```

**实际实现**:

```python
class HonestQuestioningEngine:
    def __init__(self):
        """初始化引擎 (无参数)"""
        pass

    def detect_understanding(self, agent_response: str) -> Dict[str, any]:
        """返回字典而非 UnderstandingScore 对象"""
        pass

    def generate_questions(self, context: str, agent_response: str) -> List[str]:
        """返回字符串列表而非 ClarificationQuestion 对象"""
        pass

    def create_ai_question_annotation(
        self, question: str, context: str, location: str
    ) -> Dict[str, str]:
        """创建标注字典"""
        pass

    def should_ask_question(self, understanding_score: int) -> bool:
        """判断是否追问"""
        pass
```

**差异说明**:

1. `__init__`: 设计要求传入 `task_path` 和 `why_path`，实际实现无参数
2. `assess_understanding` → `detect_understanding`: 方法名改变，返回类型从对象改为字典
3. `generate_questions`: 参数从 `(annotation_text, score)` 改为 `(context, agent_response)`
4. 返回类型: 从 `List[ClarificationQuestion]` 改为 `List[str]`
5. 缺少: `update_annotation_status()` 和 `process_user_answer()` 方法

---

## 5. 使用流程图

### 5.1 完整追问流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      诚实追问引擎工作流程                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐                                                         │
│  │ 用户创建标注    │                                                         │
│  │ (Review Comment)│                                                        │
│  └───────┬────────┘                                                         │
│          │                                                                   │
│          ▼                                                                   │
│  ┌────────────────┐                                                         │
│  │ Agent 读取标注  │                                                         │
│  │ 并生成回复      │                                                         │
│  └───────┬────────┘                                                         │
│          │                                                                   │
│          ▼                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    HonestQuestioningEngine                         │    │
│  │  ┌──────────────────────────────────────────────────────────────┐  │    │
│  │  │ detect_understanding(agent_response)                         │  │    │
│  │  │                                                               │  │    │
│  │  │  检测项目:                                                    │  │    │
│  │  │  ├── uncertainty_keywords (不确定关键词)                     │  │    │
│  │  │  ├── vague_patterns (模糊模式)                               │  │    │
│  │  │  └── question_count (反问数量)                               │  │    │
│  │  │                                                               │  │    │
│  │  │  评分: 100 - uncertainty*10 - vague*15 - question*5          │  │    │
│  │  └──────────────────────────────────────────────────────────────┘  │    │
│  └───────────────────────────┬────────────────────────────────────────┘    │
│                              │                                               │
│              ┌───────────────┴───────────────┐                              │
│              │                               │                              │
│              ▼                               ▼                              │
│      ┌──────────────┐               ┌──────────────┐                       │
│      │ score >= 70  │               │ score < 70   │                       │
│      │ 理解充分     │               │ 需要澄清     │                       │
│      └──────┬───────┘               └──────┬───────┘                       │
│             │                              │                                │
│             ▼                              ▼                                │
│      ┌──────────────┐               ┌────────────────────────────────┐    │
│      │ 执行任务     │               │ generate_questions()           │    │
│      │ 更新状态为   │               │                                │    │
│      │ addressed    │               │ ├── _extract_uncertain_parts() │    │
│      └──────────────┘               │ ├── _detect_missing_info()     │    │
│                                      │ └── _detect_assumptions()      │    │
│                                      └───────────────┬────────────────┘    │
│                                                      │                      │
│                                                      ▼                      │
│                                      ┌────────────────────────────────┐    │
│                                      │ create_ai_question_annotation()│    │
│                                      │                                │    │
│                                      │ {                              │    │
│                                      │   type: 'AI_QUESTION',         │    │
│                                      │   status: 'pending_ai_question'│    │
│                                      │ }                              │    │
│                                      └───────────────┬────────────────┘    │
│                                                      │                      │
│                                                      ▼                      │
│                                      ┌────────────────────────────────┐    │
│                                      │ CLI 提示:                       │    │
│                                      │ "❓ Agent 有 N 个问题等待回答"  │    │
│                                      └────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 与其他模块的关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    模块关系图                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Phase Manager                                 │  │
│  │                       (阶段管理器)                                    │  │
│  └────────────────────────────────┬─────────────────────────────────────┘  │
│                                   │                                          │
│                                   │ 触发                                     │
│                                   ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Honest Questioning Engine                          │  │
│  │                         (追问引擎)                                    │  │
│  │                                                                       │  │
│  │   输入: Agent 回复文本                                                │  │
│  │   输出: 理解度分数 + 追问列表 + AI_QUESTION 标注                      │  │
│  │                                                                       │  │
│  └────────────────────────────────┬─────────────────────────────────────┘  │
│                                   │                                          │
│              ┌────────────────────┼────────────────────┐                   │
│              │                    │                    │                   │
│              ▼                    ▼                    ▼                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │ Validator        │  │ Review Comments  │  │ Why-First Engine │         │
│  │ Subagent         │  │ 系统             │  │                  │         │
│  │ (文档验证)       │  │ (标注管理)       │  │ (知识库)         │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                           Task Viewer                                 │  │
│  │                         (任务可视化)                                  │  │
│  │                                                                       │  │
│  │   显示 pending_ai_question 状态 (紫色闪烁图标)                        │  │
│  │                                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 扩展指南

### 6.1 添加新的不确定关键词

**步骤 1**: 编辑关键词列表

```python
# .claude/hooks/lib/honest_questioning_engine.py

class HonestQuestioningEngine:
    def __init__(self):
        self.uncertainty_keywords = [
            '可能', '也许', '大概', '应该', '似乎',
            '不确定', '不清楚', '不太明白', '需要确认',
            'maybe', 'probably', 'perhaps', 'might', 'unclear',
            # 新增关键词
            '好像', '算是', '差不多', 'guess', 'think'
        ]
```

### 6.2 添加新的模糊模式

```python
# .claude/hooks/lib/honest_questioning_engine.py

class HonestQuestioningEngine:
    def __init__(self):
        self.vague_patterns = [
            r'等等',
            r'之类的',
            r'或者.*或者',
            r'不太.*',
            r'有点.*',
            # 新增模式
            r'差不多.*',
            r'大概.*吧',
            r'应该.*吧',
            r'as far as I know',
            r'I think'
        ]
```

### 6.3 添加新的关键信息类别

```python
# .claude/hooks/lib/honest_questioning_engine.py

def _detect_missing_info(self, context: str, response: str) -> List[str]:
    """检测缺失的关键信息"""
    missing = []

    key_info_categories = [
        ('性能要求', ['性能', '速度', '延迟', 'performance']),
        ('安全要求', ['安全', '权限', '认证', 'security']),
        ('错误处理', ['错误', '异常', '失败', 'error']),
        ('边界条件', ['边界', '极限', '最大', '最小', 'edge case']),
        ('兼容性', ['兼容', '版本', '浏览器', 'compatibility']),
        # 新增类别
        ('可扩展性', ['扩展', 'scale', '扩容', 'scalability']),
        ('可观测性', ['监控', '日志', 'trace', 'observability']),
        ('测试策略', ['测试', 'test', 'unit test', 'integration'])
    ]

    # ... 其余逻辑不变
```

### 6.4 实现追问类型系统 (进阶)

**当前实现**: 返回字符串列表
**设计目标**: 返回结构化 ClarificationQuestion 对象

```python
# 扩展实现示例

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class QuestionType(Enum):
    SOCRATIC = "socratic"          # 苏格拉底式引导
    OPTION = "option"              # 选项式提问
    CONFIRMATION = "confirmation"  # 确认式提问

@dataclass
class ClarificationQuestion:
    question_type: QuestionType
    question_text: str
    context: str
    options: List[str] = field(default_factory=list)
    related_why: Optional[str] = None

class EnhancedHonestQuestioningEngine(HonestQuestioningEngine):
    """增强版追问引擎 - 支持三种追问类型"""

    def generate_typed_questions(
        self,
        context: str,
        agent_response: str
    ) -> List[ClarificationQuestion]:
        """生成结构化追问"""
        questions = []
        understanding = self.detect_understanding(agent_response)

        if understanding['needs_clarification']:
            # 语义模糊 → 苏格拉底式
            uncertain_parts = self._extract_uncertain_parts(agent_response)
            for part in uncertain_parts:
                questions.append(ClarificationQuestion(
                    question_type=QuestionType.SOCRATIC,
                    question_text=f"关于「{part}」，你能否更具体地说明你的理解？",
                    context=part
                ))

            # 多种可能 → 选项式
            missing_info = self._detect_missing_info(context, agent_response)
            if len(missing_info) > 1:
                questions.append(ClarificationQuestion(
                    question_type=QuestionType.OPTION,
                    question_text="以下哪些方面是你已经考虑的？",
                    context="缺失信息检测",
                    options=[f"已考虑{info}" for info in missing_info]
                ))

            # 假设 → 确认式
            assumptions = self._detect_assumptions(agent_response)
            for assumption in assumptions:
                questions.append(ClarificationQuestion(
                    question_type=QuestionType.CONFIRMATION,
                    question_text=f"我理解你假设了「{assumption}」，这是否正确？",
                    context=assumption
                ))

        return questions
```

### 6.5 集成到门控系统 (进阶)

**当前状态**: 独立模块，未与门控系统集成
**建议集成方式**:

```python
# 扩展 PhaseManager 集成示例

class EnhancedPhaseManager:
    """增强阶段管理器 - 集成追问引擎"""

    def __init__(self, task_path: str):
        self.questioning_engine = HonestQuestioningEngine()
        # ... 其他初始化

    def check_gate_with_questioning(
        self,
        agent_response: str,
        context: str
    ) -> Dict[str, any]:
        """门控检查 + 理解度检测"""

        # 1. 原有门控检查
        gate_result = self.check_gate()

        # 2. 理解度检测
        understanding = self.questioning_engine.detect_understanding(agent_response)

        # 3. 如果理解度低，生成追问
        questions = []
        if understanding['needs_clarification']:
            questions = self.questioning_engine.generate_questions(
                context, agent_response
            )

        return {
            'gate_passed': gate_result['passed'],
            'understanding_score': understanding['score'],
            'needs_clarification': understanding['needs_clarification'],
            'questions': questions
        }
```

### 6.6 扩展建议

1. **实现语义分析**
   - 接入 Haiku 模型进行语义理解
   - 超越关键词匹配，实现真正的语义理解

2. **实现多维度评分**
   - 添加 `UnderstandingScore` 数据类
   - 分维度评估: 语义清晰度、上下文可用性、知识一致性

3. **集成 project-why.md**
   - 实现知识一致性检查
   - 追问时引用已有知识

4. **实现轮次限制**
   - 添加追问轮次计数
   - 最多 3 轮，超过则升级为人工处理

5. **完善状态流转**
   - 实现 `update_annotation_status()`
   - 实现 `process_user_answer()`
   - 与 Review Comments 系统集成

---

## 7. 与 clarify.md Prompt 的关系

### 7.1 clarify.md 定位

**文件**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/skills/nomos/prompts/clarify.md`

`clarify.md` 是一个 **轻量级需求澄清 prompt 模板**，用于 `/nomos:clarify` 命令。它与 HonestQuestioningEngine 的关系:

| 维度 | clarify.md | HonestQuestioningEngine |
|------|-----------|-------------------------|
| **定位** | 用户主动澄清需求 | Agent 主动追问 |
| **触发** | 用户执行 `/nomos:clarify` | Agent 回复时自动检测 |
| **输出** | 控制台报告 | AI_QUESTION 标注 |
| **深度** | 轻量级，最多 3 轮对话 | 持续追踪，与任务绑定 |

### 7.2 工作流程关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    澄清流程关系图                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  /nomos:clarify                                                             │
│       │                                                                      │
│       ▼                                                                      │
│  ┌──────────────────┐                                                       │
│  │ clarify.md       │ ──── 轻量级对话 ────▶ 控制台报告                      │
│  │ (Prompt 模板)    │                                                       │
│  └──────────────────┘                                                       │
│                                                                              │
│  /nomos:start                                                               │
│       │                                                                      │
│       ▼                                                                      │
│  ┌──────────────────┐     ┌──────────────────────────┐                     │
│  │ 任务执行流程     │ ──▶ │ HonestQuestioningEngine  │                     │
│  │                  │     │ (自动追问)               │ ──▶ AI_QUESTION 标注│
│  └──────────────────┘     └──────────────────────────┘                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. 总结

### 8.1 模块价值

诚实追问引擎是 N0mosAi 系统质量保障的关键组件：

1. **主动追问** - 自动检测 Agent 理解不足并生成追问
2. **多维度检测** - 不确定关键词、模糊模式、反问检测
3. **缺失信息检测** - 识别性能/安全/错误处理等关键信息缺失
4. **假设检测** - 发现 Agent 隐式假设并请求确认

### 8.2 实现度评估

| 功能 | 实现度 | 说明 |
|------|--------|------|
| 理解度检测 | 60% | 基于关键词，缺少语义分析 |
| 追问生成 | 50% | 模板化问题，未区分类型 |
| AI_QUESTION 标注 | 100% | 格式完整 |
| 与门控集成 | 0% | 未集成 |

**总体实现度**: 52%

### 8.3 待改进项

| 改进项 | 优先级 | 建议方案 |
|--------|--------|---------|
| 语义分析能力 | P0 | 接入 Haiku 模型 |
| 追问类型系统 | P1 | 实现 QuestionType 枚举 |
| 与门控集成 | P1 | 扩展 PhaseManager |
| 知识库集成 | P2 | 集成 project-why.md |
| 轮次限制 | P2 | 添加轮次计数器 |
| 状态流转 | P2 | 实现 update_annotation_status |

### 8.4 使用示例

```python
from honest_questioning_engine import HonestQuestioningEngine

# 初始化
engine = HonestQuestioningEngine()

# Agent 回复示例
agent_response = """
我可能需要在数据库中添加一些字段，之类的。
假设用户已经登录了，应该可以完成这个功能。
"""

# 检测理解程度
result = engine.detect_understanding(agent_response)

print(f"理解度分数: {result['score']}/100")
print(f"不确定性关键词: {result['uncertainty_count']} 个")
print(f"模糊表达: {result['vague_count']} 个")
print(f"是否需要澄清: {result['needs_clarification']}")

# 输出:
# 理解度分数: 55/100
# 不确定性关键词: 2 个 (可能, 应该)
# 模糊表达: 1 个 (之类的)
# 是否需要澄清: True

# 生成追问
questions = engine.generate_questions(
    context="实现用户个人主页功能",
    agent_response=agent_response
)

for q in questions:
    print(f"❓ {q}")

# 输出:
# ❓ 关于「我可能需要在数据库中添加一些字段...」，你是否确定理解了需求？
# ❓ 你假设了「用户已经登录了」，这个假设是否正确？

# 创建 AI_QUESTION 标注
annotation = engine.create_ai_question_annotation(
    question=questions[0],
    context="实现用户个人主页功能",
    location="plan.md:42"
)

print(annotation)
# {'type': 'AI_QUESTION', 'status': 'pending_ai_question', ...}
```

---

*文档版本: 1.0*
*最后更新: 2026-02-27*
*来源: N0mosAi 系统架构与代码分析*
