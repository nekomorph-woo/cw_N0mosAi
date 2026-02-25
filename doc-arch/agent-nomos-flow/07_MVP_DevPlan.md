# N0mosAi - MVP 阶段开发计划 (Phase 0)

> **文档版本**: 1.0
> **最后更新**: 2026-02-25
> **状态**: Draft
> **关联文档**: [06_Development_Plan_Overview.md](06_Development_Plan_Overview.md)

本文档定义 Phase 0 (MVP) 的详细开发计划，目标是验证核心刚性流程的可行性。

---

## 目录

1. [阶段目标](#1-阶段目标)
2. [Gate 0.1: 项目基础设施](#2-gate-01-项目基础设施)
3. [Gate 0.2: Task 状态管理器](#3-gate-02-task-状态管理器)
4. [Gate 0.3: AgentLinterEngine 核心](#4-gate-03-agentlinterengine-核心)
5. [Gate 0.4: 基础 Hooks](#5-gate-04-基础-hooks)
6. [Gate 0.5: 基础 SKILL](#6-gate-05-基础-skill)
7. [Gate 0.6: 文档模板](#7-gate-06-文档模板)
8. [Gate 间依赖关系](#8-gate-间依赖关系)
9. [验收标准](#9-验收标准)
10. [技术决策记录](#10-技术决策记录)

---

## 1. 阶段目标

### 1.1 目标声明

**Phase 0 目标**: 构建最小可行产品，验证「Hooks 物理门控 + Task 文件夹隔离 + Linter 强制检查」的核心闭环可行性。

### 1.2 成功标准

- [ ] 能通过 `/nomos:start` 创建任务并初始化文件夹
- [ ] PreToolUse Hook 能在代码写入前强制运行 Linter
- [ ] Stop Hook 能验证 Phase Gates 全部通过
- [ ] SessionStart Hook 能显示当前任务提示
- [ ] 一二层 Linter 规则能正常检查并输出 JSON 报告
- [ ] 能完成一个简单任务的完整刚性流程 (Research → Plan → Execute)

### 1.3 范围边界

- **包含**: 项目骨架、Task 管理、Linter 核心、基础 Hooks、基础 SKILL、文档模板
- **不包含**: Task Viewer HTML、标注系统、Why-First 引擎、Git 集成、Validator Subagent

### 1.4 阶段总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Phase 0: MVP 开发路线图                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Gate 0.1: 项目基础设施                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 目录结构 + 配置文件 + Python 包初始化                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Gate 0.2: Task 状态管理器                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Task 文件夹创建/切换 + current-task.txt + short-id-mapping.json      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Gate 0.3: AgentLinterEngine 核心          Gate 0.6: 文档模板               │
│  ┌──────────────────────────────────┐     ┌──────────────────────────┐    │
│  │ BaseRule + 一二层规则 + JSON 报告 │     │ research/plan/code_review │    │
│  └──────────────────────────────────┘     └──────────────────────────┘    │
│                              ↓                       ↓                      │
│  Gate 0.4: 基础 Hooks                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PreToolUse (Linter) + Stop (Gates) + SessionStart (提示)             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Gate 0.5: 基础 SKILL                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ /nomos + /nomos:start + /nomos:list-tasks             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Gate 0.1: 项目基础设施

### 2.1 目标

搭建项目目录结构、配置文件和 Python 包初始化，为后续 Gate 提供基础。

### 2.2 交付物

| 交付物 | 路径 | 说明 |
|--------|------|------|
| 项目根目录结构 | `.claude/` | Hooks、SKILL、配置 |
| Python 包 | `.claude/hooks/lib/` | 共享工具库 |
| 配置文件 | `.claude/settings.json` | Hooks 配置入口 |
| 忽略文件 | `.gitignore` 更新 | 排除临时文件 |

### 2.3 目录结构设计

```
project-root/
├── .claude/
│   ├── settings.json                    # Claude Code 配置 (Hooks 入口)
│   ├── current-task.txt                 # 当前活跃任务路径
│   ├── hooks/
│   │   ├── nomos-pretooluse.sh          # PreToolUse Hook 入口
│   │   ├── nomos-stop.sh               # Stop Hook 入口
│   │   ├── nomos-session-start.sh      # SessionStart Hook 入口
│   │   └── lib/
│   │       ├── __init__.py
│   │       ├── task_manager.py          # Task 状态管理器
│   │       ├── linter_engine.py         # AgentLinterEngine 核心
│   │       ├── rules/
│   │       │   ├── __init__.py
│   │       │   ├── base_rule.py         # BaseRule 接口
│   │       │   ├── layer1_syntax.py     # 第一层: 语法/风格规则
│   │       │   └── layer2_security.py   # 第二层: 安全规则
│   │       └── utils.py                 # 工具函数
│   ├── skills/
│   │   └── nomos/
│   │       ├── SKILL.md                 # SKILL 定义
│   │       └── prompts/
│   │           ├── start.md             # /nomos:start 提示词
│   │           └── list-tasks.md        # /nomos:list-tasks 提示词
│   └── templates/
│       ├── research.md                  # research.md 模板
│       ├── plan.md                      # plan.md 模板
│       ├── code_review.md              # code_review.md 模板
│       └── progress.md                 # progress.md 模板
├── tasks/
│   └── short-id-mapping.json           # 短 ID 映射表
└── project-why.md                       # 项目知识库 (初始空模板)
```

### 2.4 settings.json 配置

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "command": ".claude/hooks/nomos-pretooluse.sh $TOOL_INPUT"
      }
    ],
    "Stop": [
      {
        "command": ".claude/hooks/nomos-stop.sh"
      }
    ],
    "SessionStart": [
      {
        "command": ".claude/hooks/nomos-session-start.sh"
      }
    ]
  }
}
```

### 2.5 实施步骤

| 步骤 | 描述 | 涉及文件 | 验收条件 |
|------|------|----------|----------|
| 0.1.1 | 创建 `.claude/` 目录结构 | 目录 | 所有子目录存在 |
| 0.1.2 | 初始化 Python 包 (`__init__.py`) | `lib/__init__.py`, `rules/__init__.py` | `import` 不报错 |
| 0.1.3 | 编写 `settings.json` | `.claude/settings.json` | JSON 格式合法 |
| 0.1.4 | 创建 `tasks/` 目录和空映射文件 | `tasks/short-id-mapping.json` | 文件存在且为 `{}` |
| 0.1.5 | 创建 `project-why.md` 空模板 | `project-why.md` | 包含 YAML Frontmatter |
| 0.1.6 | 更新 `.gitignore` | `.gitignore` | 排除 `__pycache__`、`.task-viewer.html` |

### 2.6 Gate 完成条件

- [ ] 所有目录和文件已创建
- [ ] `python -c "from lib import task_manager"` 无报错
- [ ] `settings.json` 可被 Claude Code 正确加载
- [ ] `tasks/short-id-mapping.json` 为合法 JSON

---

## 3. Gate 0.2: Task 状态管理器

### 3.1 目标

实现任务文件夹的创建、切换和状态管理，支持 `current-task.txt` 和 `short-id-mapping.json`。

### 3.2 核心接口

```python
# .claude/hooks/lib/task_manager.py

import os
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class TaskInfo:
    task_id: str           # t1
    full_id: str           # t1-2026-02-25-user-login
    path: str              # tasks/t1-2026-02-25-user-login
    status: str            # draft/in_review/approved/executing/done
    created: str           # ISO 8601

class TaskManager:
    """Task 状态管理器"""

    TASKS_DIR = "tasks"
    MAPPING_FILE = "tasks/short-id-mapping.json"
    CURRENT_TASK_FILE = ".claude/current-task.txt"

    def create_task(self, task_name: str, task_type: str = "feat") -> TaskInfo:
        """
        创建新任务文件夹并初始化三件套

        Args:
            task_name: 任务名称 (如 user-login)
            task_type: 任务类型 (feat/fix/refactor/test/docs)

        Returns:
            TaskInfo 对象
        """
        pass

    def get_current_task(self) -> Optional[TaskInfo]:
        """读取 current-task.txt 获取当前任务"""
        pass

    def set_current_task(self, task_id: str) -> bool:
        """设置当前任务"""
        pass

    def list_tasks(self) -> Dict[str, TaskInfo]:
        """列出所有任务"""
        pass

    def _next_short_id(self) -> str:
        """分配下一个可用短 ID (t1, t2, ...)"""
        pass

    def _load_mapping(self) -> dict:
        """加载 short-id-mapping.json"""
        pass

    def _save_mapping(self, mapping: dict) -> None:
        """保存 short-id-mapping.json"""
        pass
```

### 3.3 任务创建流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    create_task() 流程                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  输入: task_name="user-login", task_type="feat"                             │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────────┐                                                       │
│  │ 1. 分配短 ID     │  → t1 (从 mapping 中找下一个可用)                     │
│  └────────┬─────────┘                                                       │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ 2. 生成完整 ID   │  → t1-2026-02-25-user-login                          │
│  └────────┬─────────┘                                                       │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ 3. 创建目录      │  → tasks/t1-2026-02-25-user-login/                   │
│  └────────┬─────────┘                                                       │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ 4. 初始化三件套  │  → research.md, plan.md, code_review.md, progress.md │
│  │    (从模板复制)  │                                                       │
│  └────────┬─────────┘                                                       │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ 5. 更新映射文件  │  → short-id-mapping.json                             │
│  └────────┬─────────┘                                                       │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ 6. 设置当前任务  │  → current-task.txt                                  │
│  └──────────────────┘                                                       │
│                                                                              │
│  输出: TaskInfo(task_id="t1", full_id="t1-2026-02-25-user-login", ...)     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 short-id-mapping.json 格式

```json
{
  "t1": {
    "full_id": "t1-2026-02-25-user-login",
    "path": "tasks/t1-2026-02-25-user-login",
    "status": "executing",
    "archived": false
  }
}
```

### 3.5 实施步骤

| 步骤 | 描述 | 涉及文件 | 验收条件 |
|------|------|----------|----------|
| 0.2.1 | 实现 `TaskManager` 类骨架 | `task_manager.py` | 类可实例化 |
| 0.2.2 | 实现 `_next_short_id()` | `task_manager.py` | 正确分配 t1, t2, t3... |
| 0.2.3 | 实现 `create_task()` | `task_manager.py` | 创建目录 + 四件套 + 映射 |
| 0.2.4 | 实现 `get/set_current_task()` | `task_manager.py` | 读写 current-task.txt |
| 0.2.5 | 实现 `list_tasks()` | `task_manager.py` | 返回所有任务信息 |
| 0.2.6 | 编写单元测试 | `tests/test_task_manager.py` | 所有测试通过 |

### 3.6 Gate 完成条件

- [ ] `create_task("user-login")` 成功创建目录和文件
- [ ] `get_current_task()` 返回正确的 TaskInfo
- [ ] `list_tasks()` 返回所有任务
- [ ] `short-id-mapping.json` 正确更新
- [ ] 单元测试全部通过

---

## 4. Gate 0.3: AgentLinterEngine 核心

### 4.1 目标

实现三层规则引擎的核心框架，封装 Ruff/ESLint (第一层) 和 Bandit (第二层)，输出标准 JSON 报告。

### 4.2 架构设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AgentLinterEngine 架构                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  输入: file_path + content                                                  │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    AgentLinterEngine                                  │   │
│  │                                                                       │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │   │
│  │  │  第一层规则    │  │  第二层规则    │  │  第三层规则    │         │   │
│  │  │  (语法/风格)   │  │  (安全)        │  │  (业务) [P1+]  │         │   │
│  │  │                │  │                │  │                │         │   │
│  │  │  ┌──────────┐ │  │  ┌──────────┐ │  │  ┌──────────┐ │         │   │
│  │  │  │ Ruff     │ │  │  │ Bandit   │ │  │  │ 自定义   │ │         │   │
│  │  │  │ (Python) │ │  │  │ (Python) │ │  │  │ BaseRule │ │         │   │
│  │  │  └──────────┘ │  │  └──────────┘ │  │  └──────────┘ │         │   │
│  │  │  ┌──────────┐ │  │  ┌──────────┐ │  │                │         │   │
│  │  │  │ ESLint   │ │  │  │ Semgrep  │ │  │  (Phase 1+     │         │   │
│  │  │  │ (JS/TS)  │ │  │  │ (通用)   │ │  │   才实现)      │         │   │
│  │  │  └──────────┘ │  │  └──────────┘ │  │                │         │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │                    JSON 报告生成器                               │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│         │                                                                    │
│         ▼                                                                    │
│  输出: LinterResult (JSON)                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 核心接口

```python
# .claude/hooks/lib/rules/base_rule.py

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class RuleViolation:
    rule: str              # 规则名称 (如 "ruff:E501")
    message: str           # 错误消息
    line: int              # 行号
    column: int            # 列号
    severity: Severity     # 严重程度
    suggestion: str = ""   # 修复建议
    source: str = ""       # 来源 (layer1/layer2/layer3)

@dataclass
class LinterResult:
    passed: bool
    file_path: str
    violations: List[RuleViolation] = field(default_factory=list)
    summary: str = ""

    def to_json(self) -> dict:
        """转换为 JSON 格式"""
        return {
            "passed": self.passed,
            "file_path": self.file_path,
            "violation_count": len(self.violations),
            "violations": [
                {
                    "rule": v.rule,
                    "message": v.message,
                    "line": v.line,
                    "column": v.column,
                    "severity": v.severity.value,
                    "suggestion": v.suggestion,
                    "source": v.source
                }
                for v in self.violations
            ],
            "summary": self.summary
        }

class BaseRule:
    """所有 Linter 规则的基类"""

    name: str = "base"
    layer: int = 0  # 1, 2, 3
    description: str = ""

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """
        检查代码是否违反规则

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            违规列表
        """
        raise NotImplementedError
```

```python
# .claude/hooks/lib/linter_engine.py

from typing import List, Optional
from .rules.base_rule import BaseRule, LinterResult, RuleViolation

class AgentLinterEngine:
    """核心 Linter 引擎"""

    def __init__(self):
        self.rules: List[BaseRule] = []

    def register_rule(self, rule: BaseRule) -> None:
        """注册规则"""
        self.rules.append(rule)

    def run(self, file_path: str, content: str,
            layers: Optional[List[int]] = None) -> LinterResult:
        """
        运行 Linter 检查

        Args:
            file_path: 文件路径
            content: 文件内容
            layers: 指定运行的层级 (None=全部)

        Returns:
            LinterResult
        """
        pass

    def _detect_language(self, file_path: str) -> str:
        """根据文件扩展名检测语言"""
        pass

    def _filter_rules(self, language: str,
                      layers: Optional[List[int]]) -> List[BaseRule]:
        """过滤适用的规则"""
        pass
```

### 4.4 第一层规则: Ruff 封装

```python
# .claude/hooks/lib/rules/layer1_syntax.py

import subprocess
import json
from .base_rule import BaseRule, RuleViolation, Severity

class RuffRule(BaseRule):
    """Ruff Python Linter 封装"""

    name = "ruff"
    layer = 1
    description = "Python 语法和风格检查 (Ruff)"

    def check(self, file_path: str, content: str) -> list:
        """
        调用 ruff check 并解析输出

        实现要点:
        1. 将 content 写入临时文件
        2. 运行 ruff check --output-format=json
        3. 解析 JSON 输出为 RuleViolation 列表
        4. 清理临时文件
        """
        pass

class ESLintRule(BaseRule):
    """ESLint JS/TS Linter 封装"""

    name = "eslint"
    layer = 1
    description = "JavaScript/TypeScript 语法和风格检查 (ESLint)"

    def check(self, file_path: str, content: str) -> list:
        """
        调用 eslint --format=json 并解析输出

        实现要点:
        1. 检测 eslint 是否可用
        2. 将 content 写入临时文件
        3. 运行 eslint --format=json
        4. 解析输出
        """
        pass
```

### 4.5 第二层规则: Bandit 封装

```python
# .claude/hooks/lib/rules/layer2_security.py

import subprocess
import json
from .base_rule import BaseRule, RuleViolation, Severity

class BanditRule(BaseRule):
    """Bandit Python 安全扫描封装"""

    name = "bandit"
    layer = 2
    description = "Python 安全漏洞扫描 (Bandit)"

    # 关注的安全问题类别
    SEVERITY_MAP = {
        "HIGH": Severity.ERROR,
        "MEDIUM": Severity.WARNING,
        "LOW": Severity.INFO
    }

    def check(self, file_path: str, content: str) -> list:
        """
        调用 bandit -f json 并解析输出

        实现要点:
        1. 将 content 写入临时文件
        2. 运行 bandit -f json -ll (只报告 MEDIUM+)
        3. 解析 JSON 输出
        4. 映射严重程度
        """
        pass
```

### 4.6 JSON 报告格式

```json
{
  "passed": false,
  "file_path": "src/auth/service.py",
  "violation_count": 2,
  "violations": [
    {
      "rule": "ruff:E501",
      "message": "Line too long (120 > 88 characters)",
      "line": 42,
      "column": 89,
      "severity": "warning",
      "suggestion": "将长行拆分为多行",
      "source": "layer1"
    },
    {
      "rule": "bandit:B105",
      "message": "Possible hardcoded password: 'secret_key'",
      "line": 15,
      "column": 1,
      "severity": "error",
      "suggestion": "使用环境变量或配置文件存储密钥",
      "source": "layer2"
    }
  ],
  "summary": "发现 2 个问题 (1 error, 1 warning)"
}
```

### 4.7 实施步骤

| 步骤 | 描述 | 涉及文件 | 验收条件 |
|------|------|----------|----------|
| 0.3.1 | 实现 `BaseRule` 和 `RuleViolation` | `base_rule.py` | 数据类可实例化 |
| 0.3.2 | 实现 `LinterResult.to_json()` | `base_rule.py` | 输出合法 JSON |
| 0.3.3 | 实现 `AgentLinterEngine` 骨架 | `linter_engine.py` | 注册/运行规则 |
| 0.3.4 | 实现 `RuffRule` | `layer1_syntax.py` | 检测 Python 语法问题 |
| 0.3.5 | 实现 `ESLintRule` | `layer1_syntax.py` | 检测 JS/TS 语法问题 |
| 0.3.6 | 实现 `BanditRule` | `layer2_security.py` | 检测安全漏洞 |
| 0.3.7 | 实现语言检测和规则过滤 | `linter_engine.py` | 按语言/层级过滤 |
| 0.3.8 | 编写单元测试 | `tests/test_linter_engine.py` | 所有测试通过 |

### 4.8 Gate 完成条件

- [ ] `BaseRule` 接口定义完成
- [ ] `AgentLinterEngine.run()` 能串行执行多条规则
- [ ] `RuffRule` 能检测 Python 语法问题并输出 JSON
- [ ] `BanditRule` 能检测安全漏洞并输出 JSON
- [ ] `ESLintRule` 能检测 JS/TS 问题 (或优雅降级)
- [ ] JSON 报告格式符合规范
- [ ] 单元测试全部通过

---

## 5. Gate 0.4: 基础 Hooks

### 5.1 目标

实现三个核心 Hook: PreToolUse (Linter 检查)、Stop (阶段门控)、SessionStart (任务提示)。

### 5.2 Hook 架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Hooks 门控系统 (Phase 0)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ SessionStart Hook                                                     │   │
│  │ 触发: 会话启动时                                                      │   │
│  │ 职责: 读取 current-task.txt → 显示当前任务提示                        │   │
│  │ 输出: 轻量级文本提示 (不注入完整文档)                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PreToolUse Hook                                                       │   │
│  │ 触发: Agent 调用 Write/Edit 工具时                                    │   │
│  │ 职责:                                                                 │   │
│  │   1. 检测文件类型 (Python/JS/TS)                                      │   │
│  │   2. 运行 AgentLinterEngine (一二层规则)                              │   │
│  │   3. 如果有 error → 返回 "reject" + 错误报告                         │   │
│  │   4. 如果全部通过 → 返回 "approve"                                   │   │
│  │ 超时: 5 秒                                                            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Stop Hook                                                             │   │
│  │ 触发: Agent 准备结束响应时                                            │   │
│  │ 职责:                                                                 │   │
│  │   1. 读取当前任务的 plan.md                                           │   │
│  │   2. 解析 Phase Gates (checkbox)                                      │   │
│  │   3. 检查 Review Comments 状态                                        │   │
│  │   4. 如果有未完成 Gate → 返回 "reject" + 提示                        │   │
│  │   5. 如果全部通过 → 返回 "approve"                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 PreToolUse Hook 实现

```bash
#!/bin/bash
# .claude/hooks/nomos-pretooluse.sh
# PreToolUse Hook: 在 Write/Edit 前运行 Linter

set -e

# 从 stdin 读取 tool_input JSON
TOOL_INPUT=$(cat)

# 提取文件路径和内容
FILE_PATH=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('file_path', data.get('path', '')))
")

# 跳过非代码文件
case "$FILE_PATH" in
  *.md|*.json|*.yml|*.yaml|*.txt|*.html|*.css)
    echo '{"decision": "approve"}'
    exit 0
    ;;
esac

# 运行 AgentLinterEngine
RESULT=$(python3 -c "
import sys, json
sys.path.insert(0, '.claude/hooks')
from lib.linter_engine import AgentLinterEngine
from lib.rules.layer1_syntax import RuffRule, ESLintRule
from lib.rules.layer2_security import BanditRule

engine = AgentLinterEngine()
engine.register_rule(RuffRule())
engine.register_rule(ESLintRule())
engine.register_rule(BanditRule())

# 从 stdin 读取内容
tool_input = json.loads('''$TOOL_INPUT''')
file_path = tool_input.get('file_path', tool_input.get('path', ''))
content = tool_input.get('content', '')

result = engine.run(file_path, content)
print(json.dumps(result.to_json()))
")

# 检查结果
PASSED=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['passed'])")

if [ "$PASSED" = "True" ]; then
  echo '{"decision": "approve"}'
else
  # 构造拒绝消息，包含错误详情
  echo "$RESULT" | python3 -c "
import sys, json
result = json.load(sys.stdin)
violations = result['violations']
msg = 'Linter 检查未通过:\n'
for v in violations:
    msg += f\"  - [{v['severity']}] {v['rule']}: {v['message']} (line {v['line']})\n\"
    if v.get('suggestion'):
        msg += f\"    建议: {v['suggestion']}\n\"
output = {'decision': 'reject', 'message': msg}
print(json.dumps(output))
"
fi
```

### 5.4 Stop Hook 实现

```bash
#!/bin/bash
# .claude/hooks/nomos-stop.sh
# Stop Hook: 检查 Phase Gates 和 Review Comments

set -e

# 读取当前任务
CURRENT_TASK=""
if [ -f ".claude/current-task.txt" ]; then
  CURRENT_TASK=$(cat .claude/current-task.txt)
fi

if [ -z "$CURRENT_TASK" ]; then
  echo '{"decision": "approve"}'
  exit 0
fi

# 检查 plan.md 的 Gates 和 Review Comments
python3 -c "
import sys, json, re, os

task_path = '$CURRENT_TASK'
plan_path = os.path.join(task_path, 'plan.md')

if not os.path.exists(plan_path):
    print(json.dumps({'decision': 'approve'}))
    sys.exit(0)

with open(plan_path, 'r') as f:
    content = f.read()

# 检查未完成的 Gates (未勾选的 checkbox)
unchecked_gates = re.findall(r'- \[ \] (Gate \d+\.\d+:.*)', content)

# 检查未处理的 Review Comments (CRITICAL/MAJOR + pending)
pending_reviews = []
rc_blocks = re.findall(r'### RC-\d+:.*?(?=### RC-|\Z)', content, re.DOTALL)
for block in rc_blocks:
    if 'pending' in block and ('CRITICAL' in block or 'MAJOR' in block):
        title = re.search(r'### (RC-\d+:.*)', block)
        if title:
            pending_reviews.append(title.group(1).strip())

if unchecked_gates or pending_reviews:
    msg = ''
    if unchecked_gates:
        msg += '未完成的 Gates:\n'
        for g in unchecked_gates[:5]:
            msg += f'  - [ ] {g}\n'
    if pending_reviews:
        msg += '未处理的 Review Comments:\n'
        for r in pending_reviews[:5]:
            msg += f'  - {r}\n'
    print(json.dumps({'decision': 'reject', 'message': msg}))
else:
    print(json.dumps({'decision': 'approve'}))
"
```

### 5.5 SessionStart Hook 实现

```bash
#!/bin/bash
# .claude/hooks/nomos-session-start.sh
# SessionStart Hook: 显示当前任务提示

# 读取当前任务
if [ -f ".claude/current-task.txt" ]; then
  CURRENT_TASK=$(cat .claude/current-task.txt)
  if [ -n "$CURRENT_TASK" ]; then
    TASK_ID=$(basename "$CURRENT_TASK" | cut -d'-' -f1)
    echo "📍 当前任务: $TASK_ID ($CURRENT_TASK)"
    echo "使用 /nomos:list-tasks 查看所有任务"
  else
    echo "📋 没有活跃任务。使用 /nomos:start <任务名> 开始新任务"
  fi
else
  echo "📋 没有活跃任务。使用 /nomos:start <任务名> 开始新任务"
fi
```

### 5.6 实施步骤

| 步骤 | 描述 | 涉及文件 | 验收条件 |
|------|------|----------|----------|
| 0.4.1 | 实现 `nomos-session-start.sh` | Hook 脚本 | 显示当前任务提示 |
| 0.4.2 | 实现 `nomos-pretooluse.sh` | Hook 脚本 | 拦截代码写入并运行 Linter |
| 0.4.3 | 实现 `nomos-stop.sh` | Hook 脚本 | 检查 Gates 和 Reviews |
| 0.4.4 | 配置 `settings.json` | 配置文件 | Hooks 正确注册 |
| 0.4.5 | 端到端测试 | 手动测试 | 完整流程可运行 |

### 5.7 Hook 输入输出规范

| Hook | 输入 | 输出 (approve) | 输出 (reject) |
|------|------|----------------|---------------|
| SessionStart | 无 | 文本提示 (stdout) | N/A |
| PreToolUse | `$TOOL_INPUT` (JSON) | `{"decision": "approve"}` | `{"decision": "reject", "message": "..."}` |
| Stop | 无 | `{"decision": "approve"}` | `{"decision": "reject", "message": "..."}` |

### 5.8 Gate 完成条件

- [ ] SessionStart Hook 能正确显示当前任务
- [ ] PreToolUse Hook 能拦截 Write/Edit 并运行 Linter
- [ ] PreToolUse Hook 对非代码文件 (.md/.json) 自动放行
- [ ] Stop Hook 能检测未完成的 Gates
- [ ] Stop Hook 能检测未处理的 CRITICAL/MAJOR Review Comments
- [ ] 所有 Hook 脚本有正确的错误处理
- [ ] 端到端测试通过

---

## 6. Gate 0.5: 基础 SKILL

### 6.1 目标

实现 `/nomos` 主 SKILL 和两个核心子命令: `/nomos:start` 和 `/nomos:list-tasks`。

### 6.2 SKILL 定义

```markdown
# .claude/skills/nomos/SKILL.md

---
name: nomos
description: Agent 刚性工作流管理
version: 0.1.0
commands:
  - name: start
    description: 启动新任务的刚性工作流
    args: "[task_name]"
  - name: list-tasks
    description: 列出所有任务及状态
    args: "[--status=...] [--recent=N]"
---

# /nomos

Agent 刚性工作流管理工具。通过 Hooks 物理门控确保代码质量。

## 可用命令

| 命令 | 说明 |
|------|------|
| `/nomos:start <任务名>` | 启动新任务 |
| `/nomos:list-tasks` | 列出所有任务 |
```

### 6.3 /nomos:start 提示词

```markdown
# .claude/skills/nomos/prompts/start.md

你正在执行 Nomos 的任务启动流程。

## 执行步骤

1. **创建任务文件夹**
   - 调用 TaskManager.create_task() 创建任务
   - 初始化四件套: research.md, plan.md, code_review.md, progress.md
   - 更新 current-task.txt

2. **Research 阶段**
   - 读取用户需求
   - 扫描相关代码模块
   - 生成 research.md (从模板填充)
   - 设置 research.md status: draft

3. **等待人类审阅**
   - 提示用户审阅 research.md
   - 用户在 Review Comments 区批注
   - 处理所有批注直到 addressed

4. **Plan 阶段**
   - 基于 research.md 生成 plan.md
   - 定义 Phase Gates
   - 设置 plan.md status: draft

5. **等待人类审阅**
   - 提示用户审阅 plan.md
   - 处理所有批注

6. **Execute 阶段**
   - 按 Phase Gates 逐步实现
   - 每完成一个 Gate 勾选 checkbox
   - PreToolUse Hook 自动运行 Linter

## 约束

- 每个阶段必须通过门控才能进入下一阶段
- 不能跳过 Research 直接写 Plan
- 不能跳过 Plan 直接写代码
- 所有 CRITICAL/MAJOR Review Comments 必须 addressed
```

### 6.4 /nomos:list-tasks 提示词

```markdown
# .claude/skills/nomos/prompts/list-tasks.md

列出所有任务及其状态。

## 执行步骤

1. 读取 tasks/short-id-mapping.json
2. 遍历所有任务文件夹
3. 读取每个任务的 YAML Frontmatter 获取状态
4. 按状态分组显示

## 输出格式

使用 ASCII 方框图展示:

┌─────────────────────────────────────────────────────────────────┐
│  📋 Task List                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔵 执行中                                                       │
│  └── t1-2026-02-25-user-login    [executing]   Phase 2/3       │
│                                                                  │
│  ✅ 已完成                                                       │
│  └── (无)                                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.5 实施步骤

| 步骤 | 描述 | 涉及文件 | 验收条件 |
|------|------|----------|----------|
| 0.5.1 | 编写 `SKILL.md` 定义 | `skills/nomos/SKILL.md` | SKILL 可被识别 |
| 0.5.2 | 编写 `start.md` 提示词 | `prompts/start.md` | 流程步骤清晰 |
| 0.5.3 | 编写 `list-tasks.md` 提示词 | `prompts/list-tasks.md` | 输出格式正确 |
| 0.5.4 | 端到端测试 `/nomos:start` | 手动测试 | 创建任务 + 初始化文件 |
| 0.5.5 | 端到端测试 `/nomos:list-tasks` | 手动测试 | 正确列出任务 |

### 6.6 Gate 完成条件

- [ ] `/nomos` 显示帮助信息
- [ ] `/nomos:start user-login` 创建任务文件夹和四件套
- [ ] `/nomos:list-tasks` 正确列出所有任务
- [ ] SKILL 提示词能引导 Agent 执行完整流程

---

## 7. Gate 0.6: 文档模板

### 7.1 目标

创建四件套文档模板 (research.md, plan.md, code_review.md, progress.md)，包含 YAML Frontmatter 和标准结构。

### 7.2 模板清单

| 模板 | 路径 | 核心内容 |
|------|------|----------|
| research.md | `.claude/templates/research.md` | 需求理解 + 代码调研 + Protected Interfaces + Why Questions |
| plan.md | `.claude/templates/plan.md` | 目标 + 架构设计 + Phase Gates + Review Comments |
| code_review.md | `.claude/templates/code_review.md` | 审查配置 + 变更记录 + 审查发现 + 测试结果 |
| progress.md | `.claude/templates/progress.md` | 5-Question Reboot + Session Logs + Error Log |

### 7.3 模板初始化逻辑

```python
# TaskManager.create_task() 中的模板初始化

def _init_templates(self, task_path: str, task_info: TaskInfo) -> None:
    """从模板初始化四件套，替换占位符"""

    templates_dir = ".claude/templates"
    placeholders = {
        "{TASK_ID}": task_info.task_id,
        "{FULL_ID}": task_info.full_id,
        "{CREATED}": task_info.created,
        "{STATUS}": "draft",
        "{TASK_NAME}": task_info.full_id.split("-", 1)[1] if "-" in task_info.full_id else ""
    }

    for template_name in ["research.md", "plan.md", "code_review.md", "progress.md"]:
        src = os.path.join(templates_dir, template_name)
        dst = os.path.join(task_path, template_name)

        with open(src, "r") as f:
            content = f.read()

        for key, value in placeholders.items():
            content = content.replace(key, value)

        with open(dst, "w") as f:
            f.write(content)
```

### 7.4 YAML Frontmatter 规范

所有模板文件必须包含 YAML Frontmatter:

```yaml
---
task_id: t{N}
created: YYYY-MM-DD HH:MM
status: draft
# 其他字段因模板而异
---
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `task_id` | string | 是 | 短 ID (t1, t2, ...) |
| `created` | string | 是 | 创建时间 (ISO 8601) |
| `status` | string | 是 | 文档状态 |
| `related_plan` | string | 否 | 关联的 plan.md (research.md 用) |
| `related_research` | string | 否 | 关联的 research.md (plan.md 用) |
| `current_phase` | string | 否 | 当前阶段 (plan.md 用) |

### 7.5 实施步骤

| 步骤 | 描述 | 涉及文件 | 验收条件 |
|------|------|----------|----------|
| 0.6.1 | 创建 research.md 模板 | `templates/research.md` | 包含完整结构 |
| 0.6.2 | 创建 plan.md 模板 | `templates/plan.md` | 包含 Phase Gates 和 Review Comments |
| 0.6.3 | 创建 code_review.md 模板 | `templates/code_review.md` | 包含审查层级 |
| 0.6.4 | 创建 progress.md 模板 | `templates/progress.md` | 包含 5-Question Reboot |
| 0.6.5 | 实现模板初始化逻辑 | `task_manager.py` | 占位符正确替换 |
| 0.6.6 | 创建 project-why.md 初始模板 | `project-why.md` | 包含空结构 |

### 7.6 Gate 完成条件

- [ ] 四个模板文件已创建且结构完整
- [ ] YAML Frontmatter 格式正确
- [ ] `create_task()` 能正确初始化四件套
- [ ] 占位符 (`{TASK_ID}`, `{CREATED}` 等) 正确替换
- [ ] project-why.md 初始模板已创建

---

## 8. Gate 间依赖关系

### 8.1 依赖图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Gate 依赖关系                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Gate 0.1 (基础设施)                                                        │
│     │                                                                        │
│     ├──────────────────────────────────────────────────┐                    │
│     │                                                  │                    │
│     ▼                                                  ▼                    │
│  Gate 0.2 (Task 管理器)                          Gate 0.6 (文档模板)        │
│     │                                                  │                    │
│     │                                                  │                    │
│     ├──────────────────────────────────────────────────┘                    │
│     │                                                                        │
│     ▼                                                                        │
│  Gate 0.3 (Linter Engine)                                                   │
│     │                                                                        │
│     ▼                                                                        │
│  Gate 0.4 (Hooks)                                                           │
│     │                                                                        │
│     ▼                                                                        │
│  Gate 0.5 (SKILL)                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 依赖矩阵

| Gate | 依赖 | 可并行 |
|------|------|--------|
| 0.1 基础设施 | 无 | - |
| 0.2 Task 管理器 | 0.1 | 与 0.6 并行 |
| 0.3 Linter Engine | 0.1 | 与 0.2, 0.6 并行 |
| 0.4 Hooks | 0.2, 0.3, 0.6 | 不可并行 |
| 0.5 SKILL | 0.4 | 不可并行 |
| 0.6 文档模板 | 0.1 | 与 0.2, 0.3 并行 |

### 8.3 推荐开发顺序

```
时间线 ──────────────────────────────────────────────────────────►

  Gate 0.1 ──► Gate 0.2 ──────────────────────┐
                                               │
              Gate 0.3 ──────────────────────┤──► Gate 0.4 ──► Gate 0.5
                                               │
              Gate 0.6 ──────────────────────┘
```

---

## 9. 验收标准

### 9.1 端到端验收场景

**场景: 完成一个简单任务的完整刚性流程**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MVP 端到端验收流程                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Step 1: 启动任务                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 用户: /nomos:start add-hello-world                              │   │
│  │ 期望: 创建 tasks/t1-2026-02-25-add-hello-world/                     │   │
│  │       初始化 research.md, plan.md, code_review.md, progress.md       │   │
│  │       更新 current-task.txt 和 short-id-mapping.json                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Step 2: Research 阶段                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Agent: 填充 research.md (需求理解 + 代码调研)                        │   │
│  │ 用户: 审阅并在 Review Comments 区批注                                │   │
│  │ Agent: 处理批注，标记 addressed                                      │   │
│  │ 期望: research.md status → approved                                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Step 3: Plan 阶段                                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Agent: 生成 plan.md (目标 + Phase Gates + 实施步骤)                  │   │
│  │ 用户: 审阅并批注                                                     │   │
│  │ Agent: 处理批注                                                      │   │
│  │ 期望: plan.md status → approved                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Step 4: Execute 阶段                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Agent: 按 Phase Gates 逐步实现代码                                   │   │
│  │ Hook: PreToolUse 自动运行 Linter                                     │   │
│  │   - 如果 Linter 失败 → 拒绝写入，Agent 修复后重试                   │   │
│  │   - 如果 Linter 通过 → 允许写入                                     │   │
│  │ Agent: 每完成一个 Gate 勾选 checkbox                                 │   │
│  │ 期望: 所有 Gates ✅，代码通过 Linter                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Step 5: 完成                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Hook: Stop Hook 验证所有 Gates 通过                                  │   │
│  │ 期望: Agent 正常结束响应                                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 验收 Checklist

| 验收项 | 描述 | 状态 |
|--------|------|------|
| ✅ 任务创建 | `/nomos:start` 创建完整任务结构 | [ ] |
| ✅ 文件初始化 | 四件套从模板正确初始化 | [ ] |
| ✅ Linter 拦截 | PreToolUse Hook 拦截不合格代码 | [ ] |
| ✅ Linter 放行 | PreToolUse Hook 放行合格代码 | [ ] |
| ✅ 非代码放行 | .md/.json 文件不触发 Linter | [ ] |
| ✅ Gates 检查 | Stop Hook 检测未完成 Gates | [ ] |
| ✅ Reviews 检查 | Stop Hook 检测未处理 Reviews | [ ] |
| ✅ 会话提示 | SessionStart 显示当前任务 | [ ] |
| ✅ 任务列表 | `/nomos:list-tasks` 正确显示 | [ ] |
| ✅ JSON 报告 | Linter 输出合法 JSON | [ ] |

---

## 10. 技术决策记录

### 10.1 决策清单

| 决策 | 选择 | 理由 | 替代方案 |
|------|------|------|----------|
| Hook 脚本语言 | Bash + Python | Bash 做入口和流程控制，Python 做逻辑处理 | 纯 Python (启动慢) |
| Linter 调用方式 | subprocess 调用外部工具 | 复用成熟工具，不重复造轮子 | 内置 AST 解析 (复杂) |
| 状态存储 | JSON 文件 | 简单可靠，Git 友好 | SQLite (过度设计) |
| 模板引擎 | 简单字符串替换 | MVP 阶段够用 | Jinja2 (依赖多) |
| 短 ID 格式 | t{N} (t1, t2, ...) | 简短易记 | UUID (太长) |
| Hook 超时 | Command 5s | Claude Code 默认限制 | 自定义 (不可控) |

### 10.2 已知限制

| 限制 | 影响 | 计划解决阶段 |
|------|------|-------------|
| 无 Task Viewer | 只能在 CLI 查看文档 | Phase 1 |
| 无标注系统 | 只能手动编辑 Review Comments | Phase 1 |
| 无 Why-First | 不强制深度思考 | Phase 1 |
| 无 Git 集成 | 手动 commit/branch | Phase 1 |
| 无 Validator | 无双重验证 | Phase 2 |
| 无增量检查 | 每次全量 Linter | Phase 3 |
| 第三层规则为空 | 无业务规则检查 | Phase 1+ |

---

## 附录

### A. 需求追溯矩阵

| Gate | 关联 FR | 关联 US |
|------|---------|---------|
| 0.1 基础设施 | - | - |
| 0.2 Task 管理器 | FR-004, FR-016 | US-004, US-111 |
| 0.3 Linter Engine | FR-001, FR-002, FR-007, FR-008, FR-009 | US-001, US-003 |
| 0.4 Hooks | FR-003, FR-006, FR-017 | US-005, US-103 |
| 0.5 SKILL | FR-015, FR-020 | US-110, US-113 |
| 0.6 文档模板 | FR-108 | US-004 |

### B. 文件清单

| 文件 | 类型 | Gate |
|------|------|------|
| `.claude/settings.json` | 配置 | 0.1 |
| `.claude/current-task.txt` | 状态 | 0.2 |
| `.claude/hooks/nomos-pretooluse.sh` | Hook | 0.4 |
| `.claude/hooks/nomos-stop.sh` | Hook | 0.4 |
| `.claude/hooks/nomos-session-start.sh` | Hook | 0.4 |
| `.claude/hooks/lib/__init__.py` | Python | 0.1 |
| `.claude/hooks/lib/task_manager.py` | Python | 0.2 |
| `.claude/hooks/lib/linter_engine.py` | Python | 0.3 |
| `.claude/hooks/lib/rules/__init__.py` | Python | 0.1 |
| `.claude/hooks/lib/rules/base_rule.py` | Python | 0.3 |
| `.claude/hooks/lib/rules/layer1_syntax.py` | Python | 0.3 |
| `.claude/hooks/lib/rules/layer2_security.py` | Python | 0.3 |
| `.claude/hooks/lib/utils.py` | Python | 0.1 |
| `.claude/skills/nomos/SKILL.md` | SKILL | 0.5 |
| `.claude/skills/nomos/prompts/start.md` | Prompt | 0.5 |
| `.claude/skills/nomos/prompts/list-tasks.md` | Prompt | 0.5 |
| `.claude/templates/research.md` | 模板 | 0.6 |
| `.claude/templates/plan.md` | 模板 | 0.6 |
| `.claude/templates/code_review.md` | 模板 | 0.6 |
| `.claude/templates/progress.md` | 模板 | 0.6 |
| `tasks/short-id-mapping.json` | 数据 | 0.2 |
| `project-why.md` | 知识库 | 0.6 |

---

*最后更新: 2026-02-25*
