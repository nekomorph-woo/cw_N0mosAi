# N0mosAi Linter 系统详解

本文档详细讲解 N0mosAi 项目的 Linter 系统设计与实现。

---

## 1. 概述

### 1.1 设计目标

N0mosAi Linter 系统的核心目标是实现 **"前置 Review"** -- 在代码写入之前就发现问题，而非传统的写完代码再 review。

**核心设计理念**:

```
┌──────────────────────────────────────────────────────────────┐
│                    前置审查 vs 传统审查                        │
├──────────────────────────────────────────────────────────────┤
│  传统方式:  编码 → 提交 → CI 检查 → 人工 Review → 修复        │
│  N0mosAi:  编码 → PreToolUse Linter → 阻塞/放行 → 写入       │
└──────────────────────────────────────────────────────────────┘
```

**关键价值**:

| 价值点 | 说明 |
|--------|------|
| 即时反馈 | 代码写入前立即发现问题，避免错误代码进入代码库 |
| Agent 自我修复 | Linter 结果直接喂回 Agent，自动修复问题 |
| 三层防护 | 从语法到安全再到业务，全面覆盖 |
| 零配置启动 | 默认规则开箱即用，项目可按需扩展 |

### 1.2 三层规则体系

```
┌─────────────────────────────────────────────────────────────┐
│                      三层规则金字塔                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                     ┌─────────┐                             │
│                    /  Layer 3  \                            │
│                   /   业务规则   \                           │
│                  ┌───────────────┐                          │
│                 /    Layer 2      \                         │
│                /     安全规则       \                        │
│               ┌─────────────────────┐                       │
│              /       Layer 1         \                      │
│             /       语法规则           \                     │
│            ┌───────────────────────────┐                    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 语法/类型规则 (静态分析)                          │
│           - ESLint、Ruff、TypeScript 编译器                 │
│           - 代码格式化 (Prettier、Black)                    │
│           - 导入检查、未使用变量                            │
│                                                             │
│  Layer 2: 安全/架构规则 (框架级)                            │
│           - SQL 注入检测                                    │
│           - XSS 防护检查                                    │
│           - 硬编码密钥检测                                  │
│                                                             │
│  Layer 3: 业务规则 (项目特定)                               │
│           - AI 自动生成规则                                 │
│           - 从 plan.md 解析业务规则                         │
│           - 安全沙箱执行                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Linter 系统架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              AgentLinterEngine (核心引擎)               ││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │  Layer 1: rules/layer1_syntax.py                   │││
│  │  │           RuffRule, ESLintRule                     │││
│  │  └─────────────────────────────────────────────────────┘││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │  Layer 2: rules/layer2_security.py                 │││
│  │  │           BanditRule                               │││
│  │  └─────────────────────────────────────────────────────┘││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │  Layer 3: l3_foundation/ (动态规则基础能力层)      │││
│  │  │  ├── DynamicRule + DynamicViolation               │││
│  │  │  ├── DynamicRuleLoader (安全沙箱)                  │││
│  │  │  ├── RuleGenerator (AI 生成)                       │││
│  │  │  ├── AIClient, ASTUtils, PromptBuilder            │││
│  │  │  └── task/rules/*.py (动态加载的规则脚本)          │││
│  │  └─────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────┘│
│                            ↓                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   multilang/ (多语言支持)               ││
│  │  LanguageDetector, TreeSitterEngine, LanguageRuleSet   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 文件结构

```
.claude/hooks/lib/
├── linter_engine.py          # 核心 Linter 引擎
├── utils.py                   # 工具函数
├── rules/
│   ├── __init__.py
│   ├── base_rule.py           # Layer 1/2 规则基类和数据结构
│   ├── layer1_syntax.py       # 第一层语法规则
│   └── layer2_security.py     # 第二层安全规则
├── l3_foundation/             # Layer 3 基础能力层 (新增)
│   ├── __init__.py            # 模块导出
│   ├── dynamic_rule.py        # 动态规则基类 + FileMatcher
│   ├── rule_loader.py         # 安全沙箱规则加载器
│   ├── rule_generator.py      # AI 规则生成器
│   ├── rule_context.py        # 规则上下文 (单例)
│   ├── ai_client.py           # AI 调用客户端
│   ├── ast_utils.py           # AST 解析工具 (多语言)
│   └── prompt_builder.py      # Prompt 构建器 + 模板
├── multilang/                 # 多语言支持模块
│   ├── __init__.py            # 模块导出
│   ├── language_detector.py   # 语言自动检测器
│   ├── tree_sitter_engine.py  # Tree-sitter AST 解析引擎
│   └── rulesets.py            # 分语言规则集
├── rule_examples/             # 规则示例文件 (新增)
│   ├── README.md              # 示例说明
│   ├── module_isolation.py.example
│   ├── logger_standard.py.example
│   ├── i18n_check.py.example
│   └── interface_protection.py.example
└── performance/               # 性能优化模块
    ├── cache.py               # 缓存
    ├── incremental.py         # 增量检查
    ├── parallel.py            # 并行执行
    └── lazy_loader.py         # 延迟加载
```

---

## 3. Layer 1/2 规则系统

### 3.1 数据结构定义

**文件**: `.claude/hooks/lib/rules/base_rule.py`

```python
class Severity(Enum):
    """严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class RuleViolation:
    """规则违规记录"""
    rule: str              # 规则名称 (如 "ruff:E501")
    message: str           # 错误消息
    line: int              # 行号
    column: int            # 列号
    severity: Severity     # 严重程度
    suggestion: str = ""   # 修复建议
    source: str = ""       # 来源 (layer1/layer2/layer3)


@dataclass
class LinterResult:
    """Linter 检查结果"""
    passed: bool
    file_path: str
    violations: List[RuleViolation] = field(default_factory=list)
    summary: str = ""
```

**设计要点**:

- `Severity`: 三级严重程度，只有 ERROR 级别才会阻塞写入
- `RuleViolation`: 完整的违规记录，包含修复建议
- `LinterResult`: 最终结果，可序列化为 JSON

### 3.2 规则基类

**文件**: `.claude/hooks/lib/rules/base_rule.py:59-93`

```python
class BaseRule:
    """Layer 1/2 Linter 规则基类"""

    name: str = "base"
    layer: int = 0  # 1 或 2
    description: str = ""
    supported_languages: List[str] = []  # 支持的语言列表

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """检查代码是否违反规则"""
        raise NotImplementedError(f"{self.__class__.__name__}.check() must be implemented")

    def is_applicable(self, language: str) -> bool:
        """判断规则是否适用于指定语言"""
        if not self.supported_languages:
            return True  # 如果未指定语言，则适用于所有语言
        return language in self.supported_languages
```

### 3.3 Layer 1: 语法检查

#### RuffRule (Python)

**文件**: `.claude/hooks/lib/rules/layer1_syntax.py`

```python
class RuffRule(BaseRule):
    """Ruff Python Linter 封装"""

    name = "ruff"
    layer = 1
    description = "Python 语法和风格检查 (Ruff)"
    supported_languages = ["python"]

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        # 1. 检测虚拟环境中的 ruff
        ruff_exe = _find_executable("ruff")

        # 2. 写入临时文件
        temp_file = create_temp_file(content, suffix=".py")

        # 3. 运行 ruff check --output-format=json
        result = subprocess.run(
            [ruff_exe, "check", "--output-format=json", temp_file],
            capture_output=True, text=True
        )

        # 4. 解析 JSON 输出
        for item in ruff_output:
            violations.append(RuleViolation(
                rule=f"ruff:{item.get('code', 'unknown')}",
                message=item.get('message', ''),
                line=item.get('location', {}).get('row', 0),
                column=item.get('location', {}).get('column', 0),
                severity=Severity.ERROR if code.startswith('E') else Severity.WARNING,
                source="layer1"
            ))
```

**实现要点**:

- 自动检测虚拟环境中的 ruff
- 使用临时文件确保行号准确
- 错误码以 `E` 开头的为 ERROR，其他为 WARNING

#### ESLintRule (JavaScript/TypeScript)

```python
class ESLintRule(BaseRule):
    """ESLint JS/TS Linter 封装"""

    name = "eslint"
    layer = 1
    description = "JavaScript/TypeScript 语法和风格检查 (ESLint)"
    supported_languages = ["javascript", "typescript"]

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        # ESLint 未安装时优雅降级 (不报错)
        try:
            subprocess.run(["eslint", "--version"], check=True)
        except FileNotFoundError:
            return []  # 返回空列表，不阻塞
```

### 3.4 Layer 2: 安全检查

#### BanditRule (Python 安全扫描)

**文件**: `.claude/hooks/lib/rules/layer2_security.py`

```python
class BanditRule(BaseRule):
    """Bandit Python 安全扫描封装"""

    name = "bandit"
    layer = 2
    description = "Python 安全漏洞扫描 (Bandit)"
    supported_languages = ["python"]

    SEVERITY_MAP = {
        "HIGH": Severity.ERROR,
        "MEDIUM": Severity.WARNING,
        "LOW": Severity.INFO
    }

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        # 运行 bandit -f json -ll (只报告 MEDIUM+)
        result = subprocess.run(
            [bandit_exe, "-f", "json", "-ll", temp_file],
            capture_output=True, text=True
        )
```

**内置修复建议映射** (行 132-200):

| 类别 | 示例规则 | 严重程度 | 修复建议 |
|------|---------|---------|---------|
| 密钥泄露 | B105/B106/B107 | ERROR | 使用环境变量或配置文件存储 |
| 命令注入 | B601-B607 | ERROR | 避免 shell=True |
| SQL 注入 | B608/B610/B611 | ERROR | 使用参数化查询 |
| 不安全序列化 | B301/B302 | WARNING | 考虑使用 json |
| 弱加密 | B303/B304/B305 | WARNING | 使用安全的加密算法 |

---

## 4. Layer 3: 动态规则系统

### 4.1 架构概述

Layer 3 采用 **AI 生成 + 安全沙箱** 的动态规则架构:

```
┌─────────────────────────────────────────────────────────────┐
│                  Layer 3 动态规则系统                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  规则生成流程                           ││
│  │  plan.md 业务规则 → RuleGenerator → AI 生成规则脚本    ││
│  │                            ↓                            ││
│  │                     task/rules/*.py                     ││
│  └─────────────────────────────────────────────────────────┘│
│                            ↓                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  规则加载流程                           ││
│  │  task/rules/*.py → DynamicRuleLoader → 安全沙箱执行    ││
│  │                            ↓                            ││
│  │                     DynamicRule 实例                    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 l3_foundation 模块

#### 4.2.1 模块导出

**文件**: `.claude/hooks/lib/l3_foundation/__init__.py`

```python
from .dynamic_rule import DynamicRule, DynamicViolation, Severity, FileMatcher
from .ai_client import AIClient
from .ast_utils import ASTUtils
from .prompt_builder import PromptBuilder, PromptTemplate
from .rule_context import RuleContext
from .rule_loader import DynamicRuleLoader, load_rules_from_task, SecurityError
from .rule_generator import RuleGenerator, RuleSyncer, RuleSpec, generate_rules_from_plan
```

#### 4.2.2 DynamicRule 基类

**文件**: `.claude/hooks/lib/l3_foundation/dynamic_rule.py`

```python
@dataclass
class DynamicViolation:
    """动态规则违规记录 - Layer 3 专用"""
    rule: str              # 规则名称
    message: str           # 违规描述
    line: int              # 行号
    column: int            # 列号
    severity: Severity     # 严重程度
    suggestion: str = ""   # 修复建议
    source: str = "layer3" # 来源


class DynamicRule:
    """动态规则基类 - Layer 3 业务规则必须继承此类

    与 BaseRule (rules/base_rule.py) 的区别:
    - BaseRule: 用于 Layer 1/2 静态规则，有 supported_languages, is_applicable()
    - DynamicRule: 用于 Layer 3 动态规则，有 handler_type, config, should_check()
    """

    name: str = ""              # 规则名称
    layer: int = 3              # 规则层级 (固定为 3)
    description: str = ""       # 规则描述
    handler_type: str = "command"  # handler 类型: command / prompt

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def check(self, file_path: str, content: str) -> List[DynamicViolation]:
        """检查代码是否违规"""
        raise NotImplementedError("子类必须实现 check() 方法")

    def should_check(self, file_path: str) -> bool:
        """判断是否需要检查此文件"""
        return True  # 默认检查所有文件
```

#### 4.2.3 FileMatcher 工具

**文件**: `.claude/hooks/lib/l3_foundation/dynamic_rule.py:98-194`

```python
class FileMatcher:
    """文件匹配工具 - 用于 should_check 实现"""

    @staticmethod
    def match_patterns(file_path: str, patterns: List[str]) -> bool:
        """
        检查文件路径是否匹配任意模式

        支持的模式格式:
        - `*.py`: 匹配所有 .py 文件
        - `**/*.py`: 递归匹配所有 .py 文件
        - `src/api/**/*.py`: 匹配 src/api/ 下的所有 .py 文件
        - `*.ts,*.tsx`: 支持多个模式 (逗号分隔)
        """
        for pattern in patterns:
            # 处理 ** 模式
            if "**" in pattern:
                # 转换为 fnmatch 兼容格式
                ...

            # fnmatch 匹配
            if fnmatch.fnmatch(normalized_path, normalized_pattern):
                return True

        return False

    @staticmethod
    def match_extensions(file_path: str, extensions: List[str]) -> bool:
        """检查文件扩展名是否匹配"""
        return any(file_path.endswith(ext) for ext in extensions)
```

### 4.3 规则加载器 (安全沙箱)

**文件**: `.claude/hooks/lib/l3_foundation/rule_loader.py`

#### 4.3.1 三重安全检查

```python
class DynamicRuleLoader:
    """动态规则加载器 - 从 task 目录加载规则脚本"""

    def _load_script_securely(self, script_path: Path) -> List[DynamicRule]:
        """安全加载单个脚本"""

        # 1. 读取脚本内容
        source = script_path.read_text(encoding='utf-8')

        # 2. 静态安全扫描 (正则匹配危险模式)
        threats = self._static_security_scan(source)
        if threats:
            raise SecurityError(f"静态扫描检测到威胁: {', '.join(threats)}")

        # 3. AST 安全检查
        ast_threats = self._ast_security_check(source)
        if ast_threats:
            raise SecurityError(f"AST 检查检测到威胁: {', '.join(ast_threats)}")

        # 4. 创建沙箱环境
        sandbox_globals = self._create_sandbox_globals()

        # 5. 编译代码
        code = compile(source, str(script_path), "exec")

        # 6. 沙箱执行 (带超时)
        self._exec_with_timeout(code, sandbox_globals, timeout=5)

        # 7. 提取规则实例
        ...
```

#### 4.3.2 静态安全扫描

```python
def _static_security_scan(self, source: str) -> List[str]:
    """静态安全扫描 - 正则匹配危险模式"""
    dangerous_patterns = [
        (r"import\s+os\b", "禁止导入 os 模块"),
        (r"import\s+subprocess", "禁止导入 subprocess 模块"),
        (r"import\s+sys\b", "禁止导入 sys 模块"),
        (r"\beval\s*\(", "禁止使用 eval()"),
        (r"\bexec\s*\(", "禁止使用 exec()"),
        (r"\bopen\s*\(", "禁止使用 open()"),
        (r"__builtins__", "禁止访问 __builtins__"),
    ]
    ...
```

#### 4.3.3 沙箱执行环境

```python
def _create_sandbox_globals(self) -> Dict[str, Any]:
    """创建沙箱执行环境"""
    # 1. 创建受限的 builtins
    safe_builtins = {
        "__build_class__": __builtins__["__build_class__"],
        "abs": abs, "all": all, "any": any, "bool": bool,
        "dict": dict, "list": list, "set": set, "str": str,
        "Exception": Exception, "ValueError": ValueError,
        # 禁止的函数 (设为 None)
        "eval": None, "exec": None, "open": None,
    }

    # 2. 注入白名单模块
    return {
        "__builtins__": safe_builtins,
        # 注入 l3_foundation 基础能力
        "DynamicRule": DynamicRule,
        "DynamicViolation": DynamicViolation,
        "Severity": Severity,
        "FileMatcher": FileMatcher,
        "AIClient": AIClient,
        "ASTUtils": ASTUtils,
        "re": re, "ast": ast,
    }
```

#### 4.3.4 规则风格支持

```python
def _load_script_securely(self, script_path: Path) -> List[DynamicRule]:
    ...
    # 方式 1: 类继承风格 (继承 DynamicRule)
    if issubclass(obj, DynamicRule) and obj is not DynamicRule:
        rule_instance = obj()
        rules.append(rule_instance)

    # 方式 2: 函数式风格 (有 check 和 should_check 函数)
    if name == "check" and callable(obj):
        # 检查是否有函数式规则的标识 (name, layer, handler_type)
        if sandbox_globals.get("name"):
            class FunctionalRuleWrapper(DynamicRule):
                def check(self, file_path, content):
                    return self._check_fn(file_path, content)
                def should_check(self, file_path):
                    return self._should_check_fn(file_path)
            rules.append(FunctionalRuleWrapper())
```

### 4.4 规则生成器

**文件**: `.claude/hooks/lib/l3_foundation/rule_generator.py`

#### 4.4.1 从 plan.md 解析业务规则

```python
class RuleGenerator:
    """规则生成器 - 从 plan.md 生成规则脚本"""

    def parse_business_rules(self, plan_content: str = None) -> List[RuleSpec]:
        """
        从 plan.md 解析业务规则

        支持的格式:
        #### 规则 1: 规则名称
        - **描述**: 规则描述
        - **Handler**: command / prompt
        - **严重程度**: error / warning / info
        - **文件匹配**: src/api/**/*.py
        - **适用范围**: API 层代码
        - **代码特征**: 带路由装饰器的函数
        - **详细说明**: ...
        """
        # 查找 "## 业务规则" 章节
        # 解析规则属性
        ...
```

#### 4.4.2 AI 生成规则脚本

```python
def generate_rule_script(self, rule_spec: RuleSpec) -> Optional[str]:
    """生成规则脚本"""
    # 选择模板
    template = (PROMPT_HANDLER_TEMPLATE if rule_spec.handler_type == "prompt"
                else COMMAND_HANDLER_TEMPLATE)

    # 填充模板
    prompt = template.render(
        task_id=self.context.task_id,
        rule_description=self._format_rule_description(rule_spec)
    )

    # 调用 AI 生成
    result = self.ai_client.call(prompt, "", max_tokens=4096)

    # 提取 Python 代码块
    code_match = re.search(r'```python\s*([\s\S]*?)\s*```', result)
    return code_match.group(1) if code_match else None
```

#### 4.4.3 规则同步器

```python
class RuleSyncer:
    """规则同步器 - plan.md 变更时同步规则脚本"""

    def sync_on_plan_change(self, old_plan: str, new_plan: str) -> Dict[str, Any]:
        """plan.md 变更时同步规则脚本"""
        old_rules = self.generator.parse_business_rules(old_plan)
        new_rules = self.generator.parse_business_rules(new_plan)

        diff = self._compute_diff(old_rules, new_rules)

        # 处理新增/修改/删除规则
        # 如果用户已修改规则脚本，跳过自动更新
        ...
```

### 4.5 AI 客户端

**文件**: `.claude/hooks/lib/l3_foundation/ai_client.py`

#### 4.5.1 零配置设计

```python
class AIClient:
    """
    轻量级 AI 客户端 - 零配置设计

    环境变量 (优先级递减):
      API Key: ANTHROPIC_API_KEY > ANTHROPIC_AUTH_TOKEN > NOMOS_API_KEY
      Base URL: ANTHROPIC_BASE_URL > NOMOS_API_BASE_URL
      Model: ANTHROPIC_DEFAULT_HAIKU_MODEL > DEFAULT_HAIKU_MODEL
      Timeout: NOMOS_AI_TIMEOUT (默认 30 秒)
    """

    DEFAULT_MODEL = "claude-3-5-haiku-20241022"
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    MAX_RETRIES = 3

    def __init__(self):
        # 读取环境变量配置
        self.api_key = (
            os.environ.get("ANTHROPIC_API_KEY") or
            os.environ.get("NOMOS_API_KEY") or
            ...
        )
```

#### 4.5.2 调用机制

```python
def call(self, prompt: str, content: str, max_tokens: int = 512) -> Optional[Dict]:
    """调用 AI 进行判断 (带重试机制)"""
    # 1. 检查缓存
    cache_key = hashlib.md5(f"{prompt}:{content}".encode()).hexdigest()
    if cache_key in self._cache:
        return self._cache[cache_key]

    # 2. 重试机制 (指数退避)
    for attempt in range(self.MAX_RETRIES):
        try:
            result = self._make_request(url, request_body)
            # 3. 解析 JSON (支持 markdown 代码块)
            parsed = self._parse_response(result)
            self._cache[cache_key] = parsed
            return parsed
        except Exception as e:
            time.sleep(1 * (attempt + 1))
            continue

    return None
```

### 4.6 Handler 类型

Layer 3 支持两种 Handler 类型:

```
┌─────────────────────────────────────────────────────────────┐
│                  Layer 3 Handler 类型                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Command Handler (静态检查)                                 │
│  ├── 使用 ASTUtils 进行静态分析                             │
│  ├── 速度快，确定性高                                       │
│  └── 示例: module_isolation, interface_protection          │
│                                                             │
│  Prompt Handler (语义判断)                                  │
│  ├── 使用 AIClient 进行 AI 语义分析                         │
│  ├── 能处理复杂的语义场景                                   │
│  ├── 正则降级: AI 不可用时使用正则                          │
│  └── 示例: logger_standard, i18n_check                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Prompt 模板

**文件**: `.claude/hooks/lib/l3_foundation/prompt_builder.py`

```python
COMMAND_HANDLER_TEMPLATE = """你是 Python 代码生成专家。根据用户的业务规则需求，生成 Layer 3 规则脚本。

## 生成要求

1. **Handler 类型**: Command Handler (使用 AST 静态分析)
2. **脚本模板**: 必须继承 DynamicRule
3. **基础能力**: 必须使用 l3_foundation 提供的能力
   - DynamicRule, DynamicViolation, Severity
   - ASTUtils, FileMatcher, RuleContext

4. **规则范围理解**:
   - **适用范围**: 用户描述的代码范围 (如 "API 层代码")
   - **文件匹配**: 具体的 glob 模式 (如 `src/api/**/*.py`)
   - **代码特征**: 进一步限定检查目标的特征

5. **should_check 实现**: 使用 FileMatcher.match_patterns() 过滤文件
6. **check 实现**: 使用 ASTUtils.parse() 解析代码，实现检查逻辑
"""

PROMPT_HANDLER_TEMPLATE = """...
1. **Handler 类型**: Prompt Handler (使用 AI 语义分析)
...
5. **检查逻辑**:
   - 实现 _should_ai_check() 快速预检
   - 实现 _build_prompt() 构建 AI prompt
   - 实现 _parse_ai_result() 解析 AI 返回
   - 实现 _fallback_check() 正则降级
"""
```

---

## 5. 规则示例

### 5.1 示例文件目录

**位置**: `.claude/hooks/lib/rule_examples/`

| 示例文件 | Handler 类型 | 说明 |
|---------|-------------|------|
| `module_isolation.py.example` | Command | 模块隔离检查 - 演示 AST 检查导入 |
| `logger_standard.py.example` | Prompt | Logger 规范 - 演示 AI 语义判断 + 正则降级 |
| `i18n_check.py.example` | Prompt | 国际化检查 - 演示 UI 文本检查 |
| `interface_protection.py.example` | Command | 接口保护 - 演示签名变更检查 |

### 5.2 Command Handler 示例

**文件**: `rule_examples/module_isolation.py.example`

```python
# 规则元信息
name = "module_isolation"
layer = 3
handler_type = "command"
description = "检查模块间 import 是否符合隔离规则"

# 规则配置
config = {
    'allowed_imports': ["src.core", "src.utils"],
    'forbidden_imports': ["src.internal"],
    'target_patterns': ["*.py"]
}

def check(file_path, content):
    """检查代码是否违反模块隔离规则"""
    violations = []

    # 使用 ASTUtils 提取导入语句
    tree = ASTUtils.parse(content, file_path)
    imports = ASTUtils.find_imports(tree)

    for imp in imports:
        module = imp.get('module', '')

        # 检查是否在禁止列表中
        for forbidden in config.get('forbidden_imports', []):
            if module.startswith(forbidden):
                violations.append(DynamicViolation(
                    rule=name,
                    message=f"禁止导入模块 '{module}'",
                    line=imp.get('line', 0),
                    column=0,
                    severity=Severity.ERROR,
                    suggestion=f"请使用允许的模块: {', '.join(config.get('allowed_imports', []))}"
                ))

    return violations

def should_check(file_path):
    """判断是否需要检查此文件"""
    return FileMatcher.match_patterns(file_path, config.get('target_patterns', ["*.py"]))
```

### 5.3 Prompt Handler 模板

```python
# 规则元信息
name = "rule_name"
layer = 3
handler_type = "prompt"
description = "规则描述"

config = {
    "scope": "前端组件",
    "target_patterns": ["src/**/*.tsx"],
    "code_features": "包含用户可见文本的组件",
}

ai_client = AIClient()

def check(file_path, content):
    """智能检查: AI 优先, 正则降级"""
    violations = []

    # 快速预检
    if not _should_check(file_path, content):
        return violations

    # AI 判断
    if ai_client.available:
        prompt = _build_prompt()
        result = ai_client.call(prompt, content)
        if result:
            violations = _parse_ai_result(result)

    # 降级到正则
    if not violations:
        violations = _fallback_check(file_path, content)

    return violations

def _should_check(file_path, content):
    """快速预检"""
    return True

def _build_prompt():
    """构建 AI prompt"""
    return """你是代码审查专家..."""

def _parse_ai_result(result):
    """解析 AI 返回结果"""
    return []

def _fallback_check(file_path, content):
    """正则降级检查"""
    return []

def should_check(file_path):
    return FileMatcher.match_patterns(file_path, config.get("target_patterns", ["*"]))
```

---

## 6. 核心 Linter 引擎

### 6.1 AgentLinterEngine

**文件**: `.claude/hooks/lib/linter_engine.py`

```python
class AgentLinterEngine:
    """核心 Linter 引擎"""

    def __init__(self):
        self.rules: List[BaseRule] = []

    def register_rule(self, rule: BaseRule) -> None:
        """注册规则"""
        self.rules.append(rule)

    def run(self, file_path: str, content: str,
            layers: Optional[List[int]] = None) -> LinterResult:
        """运行 Linter 检查"""
        # 1. 检测语言
        language = self._detect_language(file_path)
        if not language:
            return LinterResult(passed=True, summary="非代码文件，跳过检查")

        # 2. 过滤适用的规则
        applicable_rules = self._filter_rules(language, layers)

        # 3. 执行所有规则
        all_violations = []
        for rule in applicable_rules:
            try:
                violations = rule.check(file_path, content)
                all_violations.extend(violations)
            except Exception as e:
                # 规则执行失败，记录为警告
                all_violations.append(RuleViolation(...))

        # 4. 判断是否通过（只有 ERROR 才算失败）
        errors = [v for v in all_violations if v.severity == Severity.ERROR]
        passed = len(errors) == 0

        return LinterResult(passed=passed, violations=all_violations, ...)
```

### 6.2 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentLinterEngine.run()                  │
├─────────────────────────────────────────────────────────────┤
│  Step 1: 检测语言                                           │
│          └── utils.detect_language(file_path)               │
│                                                             │
│  Step 2: 过滤规则                                           │
│          ├── 按层级过滤 (layers 参数)                       │
│          └── 按语言过滤 (is_applicable)                     │
│                                                             │
│  Step 3: 执行规则                                           │
│          ├── Layer 1: RuffRule / ESLintRule                 │
│          ├── Layer 2: BanditRule                            │
│          └── Layer 3: DynamicRule (从 task/rules/ 加载)    │
│                                                             │
│  Step 4: 汇总结果                                           │
│          ├── passed = (errors == 0)                         │
│          └── 生成摘要                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 使用示例

### 7.1 基本使用

```python
from lib.linter_engine import AgentLinterEngine
from lib.rules.layer1_syntax import RuffRule, ESLintRule
from lib.rules.layer2_security import BanditRule
from lib.l3_foundation import load_rules_from_task

# 创建引擎
engine = AgentLinterEngine()

# 注册 Layer 1/2 规则
engine.register_rule(RuffRule())
engine.register_rule(ESLintRule())
engine.register_rule(BanditRule())

# 加载 Layer 3 动态规则
dynamic_rules = load_rules_from_task("tasks/t1-feature")
for rule in dynamic_rules:
    engine.register_rule(rule)

# 运行检查
result = engine.run("src/auth/service.py", python_code)

if result.passed:
    print("✅ 检查通过")
else:
    print(f"❌ 发现 {len(result.violations)} 个问题")
    for v in result.violations:
        print(f"  [{v.severity.value}] {v.rule}: {v.message} (line {v.line})")
```

### 7.2 按层级过滤

```python
# 只运行 Layer 1 (语法检查)
result = engine.run("src/auth/service.py", content, layers=[1])

# 只运行 Layer 2 和 Layer 3
result = engine.run("src/auth/service.py", content, layers=[2, 3])
```

### 7.3 生成规则脚本

```python
from lib.l3_foundation import generate_rules_from_plan

# 从 plan.md 生成所有规则脚本
generated = generate_rules_from_task("tasks/t1-feature")
for path in generated:
    print(f"✅ 规则脚本已生成: {path}")
```

### 7.4 结果序列化

```python
result = engine.run("src/auth/service.py", content)

# 转换为 JSON
json_result = result.to_json()
# {
#   "passed": false,
#   "file_path": "src/auth/service.py",
#   "violation_count": 3,
#   "violations": [...],
#   "summary": "发现 3 个问题 (1 error, 2 warning)"
# }
```

---

## 8. 扩展指南

### 8.1 添加 Layer 1/2 规则

```python
# .claude/hooks/lib/rules/layer1_syntax.py

class GolangCILintRule(BaseRule):
    """golangci-lint Go Linter 封装"""

    name = "golangci-lint"
    layer = 1
    description = "Go 语法和风格检查"
    supported_languages = ["go"]

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        temp_file = create_temp_file(content, suffix=".go")
        result = subprocess.run(
            ["golangci-lint", "run", "--output-format=json", temp_file],
            capture_output=True, text=True
        )
        # 解析输出...
```

### 8.2 添加 Layer 3 业务规则

**方式 1: 在 plan.md 中定义**

```markdown
## 业务规则

#### 规则 1: Trace ID 传递检查

- **描述**: 所有服务调用必须传递 trace_id 参数
- **适用范围**: Service 层代码
- **文件匹配**: src/services/**/*.py
- **代码特征**: 调用其他服务的函数
- **Handler**: `command`
- **严重程度**: `warning`
```

**方式 2: 手动编写规则脚本**

```python
# tasks/t1-feature/rules/trace_id_check.py

name = "trace_id_check"
layer = 3
handler_type = "command"
description = "检查 trace_id 是否正确传递"

config = {
    "service_modules": ["src/services/"],
}

def check(file_path, content):
    violations = []
    tree = ASTUtils.parse(content, file_path)
    calls = ASTUtils.find_function_calls(tree, "*")

    for call in calls:
        # 检查是否传递了 trace_id
        if "trace_id" not in call.get("args", ""):
            violations.append(DynamicViolation(
                rule=name,
                message=f"调用 {call['function']} 未传递 trace_id",
                line=call["line"],
                column=0,
                severity=Severity.WARNING
            ))

    return violations

def should_check(file_path):
    return FileMatcher.match_patterns(file_path, config.get("service_modules", []))
```

---

## 9. 设计 vs 实现对比

### 9.1 完成度分析

```
┌─────────────────────────────────────────────────────────────┐
│                     设计 vs 实现对比                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1 (语法规则)                                         │
│  ├── RuffRule     ✅ 完整实现                               │
│  └── ESLintRule   ✅ 完整实现                               │
│                                                             │
│  Layer 2 (安全规则)                                         │
│  └── BanditRule   ✅ 完整实现 (含完整修复建议映射)          │
│                                                             │
│  Layer 3 (业务规则)                                         │
│  ├── l3_foundation/         ✅ 独立模块实现                 │
│  ├── DynamicRule            ✅ 完整实现                     │
│  ├── DynamicRuleLoader      ✅ 安全沙箱实现                 │
│  ├── RuleGenerator          ✅ AI 生成实现                  │
│  ├── RuleSyncer             ✅ plan.md 同步实现             │
│  ├── AIClient               ✅ 零配置设计实现               │
│  ├── ASTUtils               ✅ 多语言支持实现               │
│  └── rule_examples/         ✅ 4 个示例                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 架构演进

| 方面 | 原设计 | 当前实现 |
|------|--------|---------|
| Layer 3 位置 | `rules/layer3_business.py` | 独立 `l3_foundation/` 模块 |
| 规则来源 | plan.md YAML Frontmatter | plan.md "## 业务规则" 章节 |
| 规则加载 | 直接实例化 | 安全沙箱 + 动态加载 |
| 规则生成 | 手动编写 | AI 自动生成 |
| 规则风格 | 仅类继承 | 类继承 + 函数式 |

---

## 10. 总结

N0mosAi Linter 系统通过三层规则体系，实现了从语法到业务的全面代码审查。核心特点包括:

1. **前置审查**: 在代码写入前拦截问题
2. **三层防护**: Layer 1 (语法) → Layer 2 (安全) → Layer 3 (业务)
3. **AI 生成**: Layer 3 规则可从 plan.md 自动生成
4. **安全沙箱**: 动态规则在受限环境中执行
5. **多语言支持**: 通过 multilang 模块支持多语言 AST 解析

当前实现已完成核心框架和所有规则层，AI 规则生成和安全沙箱是 Layer 3 的核心能力。

---

*文档版本: 2.0*
*最后更新: 2026-02-28*
*来源: N0mosAi 系统架构与代码分析*
