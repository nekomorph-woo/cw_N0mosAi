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
│           - i18n 强制使用                                   │
│           - 模块隔离规则                                    │
│           - plan.md 中定义的动态规则                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构设计

### 2.1 架构文档中的设计要求

来源: `/Volumes/Under_M2/a056cw/cw_N0mosAi/doc-arch/agent-nomos-flow/03_System_Architecture.md:820-853`

```
┌─────────────────────────────────────────────────────────────┐
│                      规则引擎层                              │
│  (AgentLinterEngine + 三层规则体系)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      状态持久化层                            │
│  (Task 文件夹 + project-why.md + .claude/)                  │
└─────────────────────────────────────────────────────────────┘
```

**设计要点**:

1. **三层规则体系**: 从语法到业务全覆盖
2. **接口设计**:
   ```python
   class BaseRule:
       def check(self, code, context) -> RuleResult:
           pass

   class AgentLinterEngine:
       def run_all_rules(self, code, layer) -> List[RuleResult]:
           pass
   ```

3. **触发时机**: PreToolUse Hook (工具调用前)

### 2.2 审查流程中的位置

```
┌─────────────────────────────────────────────────────────────────────┐
│                      三层规则审查流程                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Agent 调用 Write/Edit                                              │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    PreToolUse Hook                               ││
│  │  ┌─────────────────────────────────────────────────────────────┐││
│  │  │              AgentLinterEngine.run()                        │││
│  │  │                                                              │││
│  │  │   Layer 1: Ruff/ESLint ────────────┐                        │││
│  │  │                                     │                        │││
│  │  │   Layer 2: Bandit (安全) ───────────┼───▶ 汇总结果          │││
│  │  │                                     │                        │││
│  │  │   Layer 3: 业务规则 ────────────────┘                        │││
│  │  └─────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────┘│
│       │                                                              │
│       ├── PASS ──▶ 允许工具执行                                      │
│       │                                                              │
│       └── FAIL ──▶ 阻塞 + 错误喂回 Agent                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 代码实现详解

### 3.1 文件结构

```
.claude/hooks/lib/
├── linter_engine.py          # 核心 Linter 引擎
├── utils.py                   # 工具函数
├── rules/
│   ├── __init__.py
│   ├── base_rule.py           # 规则基类和数据结构
│   ├── layer1_syntax.py       # 第一层语法规则
│   ├── layer2_security.py     # 第二层安全规则
│   └── layer3_business.py     # 第三层业务规则
└── multilang/                 # 多语言支持模块
    ├── __init__.py            # 模块导出
    ├── language_detector.py   # 语言自动检测器
    ├── tree_sitter_engine.py  # Tree-sitter AST 解析引擎
    └── rulesets.py            # 分语言规则集
```

### 3.2 数据结构定义

**文件**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/hooks/lib/rules/base_rule.py`

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

**设计分析**:

- `Severity`: 三级严重程度，只有 ERROR 级别才会阻塞写入
- `RuleViolation`: 完整的违规记录，包含修复建议
- `LinterResult`: 最终结果，可序列化为 JSON

### 3.3 规则基类

**文件**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/hooks/lib/rules/base_rule.py:59-93`

```python
class BaseRule:
    """所有 Linter 规则的基类"""

    name: str = "base"
    layer: int = 0  # 1, 2, 3
    description: str = ""
    supported_languages: List[str] = []  # 支持的语言列表

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """
        检查代码是否违反规则

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            违规列表
        """
        raise NotImplementedError(f"{self.__class__.__name__}.check() must be implemented")

    def is_applicable(self, language: str) -> bool:
        """
        判断规则是否适用于指定语言
        """
        if not self.supported_languages:
            return True  # 如果未指定语言，则适用于所有语言
        return language in self.supported_languages
```

**设计亮点**:

1. **类属性声明**: `name`, `layer`, `description` 作为类属性，便于反射和注册
2. **语言过滤**: `is_applicable()` 支持多语言项目
3. **强制实现**: `check()` 抛出 `NotImplementedError`，确保子类实现

### 3.4 核心 Linter 引擎

**文件**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/hooks/lib/linter_engine.py`

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
        """
        运行 Linter 检查

        Args:
            file_path: 文件路径
            content: 文件内容
            layers: 指定运行的层级 (None=全部)

        Returns:
            LinterResult
        """
        # 1. 检测语言
        language = self._detect_language(file_path)
        if not language:
            return LinterResult(passed=True, file_path=file_path,
                               summary="非代码文件，跳过检查")

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

        return LinterResult(passed=passed, ...)
```

**执行流程**:

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
│          ├── rule.check(file_path, content)                 │
│          └── 异常捕获 → 转为 WARNING                        │
│                                                             │
│  Step 4: 汇总结果                                           │
│          ├── passed = (errors == 0)                         │
│          └── 生成摘要                                       │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 第一层规则: 语法检查

**文件**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/hooks/lib/rules/layer1_syntax.py`

#### 3.5.1 RuffRule (Python)

```python
class RuffRule(BaseRule):
    """Ruff Python Linter 封装"""

    name = "ruff"
    layer = 1
    description = "Python 语法和风格检查 (Ruff)"
    supported_languages = ["python"]

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        # 1. 检查 ruff 是否可用
        ruff_exe = _find_executable("ruff")
        try:
            subprocess.run([ruff_exe, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return [RuleViolation(rule="ruff:not_found", ...)]

        # 2. 写入临时文件
        temp_file = create_temp_file(content, suffix=".py")

        try:
            # 3. 运行 ruff check
            result = subprocess.run(
                [ruff_exe, "check", "--output-format=json", temp_file],
                capture_output=True, text=True
            )

            # 4. 解析 JSON 输出
            if result.stdout:
                ruff_output = json.loads(result.stdout)
                for item in ruff_output:
                    violations.append(RuleViolation(
                        rule=f"ruff:{item.get('code', 'unknown')}",
                        message=item.get('message', ''),
                        line=item.get('location', {}).get('row', 0),
                        column=item.get('location', {}).get('column', 0),
                        severity=Severity.ERROR if item.get('code', '').startswith('E') else Severity.WARNING,
                        ...
                    ))
        finally:
            os.remove(temp_file)

        return violations
```

**实现要点**:

- 使用临时文件而非 stdin，确保行号准确
- 错误码以 `E` 开头的为 ERROR，其他为 WARNING
- 自动检测虚拟环境中的 ruff

#### 3.5.2 ESLintRule (JavaScript/TypeScript)

```python
class ESLintRule(BaseRule):
    """ESLint JS/TS Linter 封装"""

    name = "eslint"
    layer = 1
    description = "JavaScript/TypeScript 语法和风格检查 (ESLint)"
    supported_languages = ["javascript", "typescript"]

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        # 检查 eslint 是否可用
        try:
            subprocess.run(["eslint", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []  # ESLint 未安装，优雅降级

        # ... 类似 RuffRule 的处理流程
```

**差异点**: ESLint 未安装时不报错，优雅降级（返回空列表）

### 3.6 第二层规则: 安全检查

**文件**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/hooks/lib/rules/layer2_security.py`

#### 3.6.1 BanditRule (Python 安全扫描)

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

        # 解析并映射严重程度
        for issue in bandit_output.get('results', []):
            severity_str = issue.get('issue_severity', 'LOW')
            severity = self.SEVERITY_MAP.get(severity_str, Severity.INFO)
            violations.append(RuleViolation(
                rule=f"bandit:{issue.get('test_id', 'unknown')}",
                message=issue.get('issue_text', ''),
                ...
            ))
```

**内置修复建议** (行 132-200):

```python
def _get_suggestion(self, test_id: str) -> str:
    """根据测试 ID 提供修复建议"""
    suggestions = {
        "B105": "使用环境变量或配置文件存储密钥",
        "B106": "使用环境变量或配置文件存储密码",
        "B301": "避免使用 pickle，考虑使用 json",
        "B311": "使用 secrets 模块替代 random",
        "B506": "避免使用不安全的 YAML 加载",
        "B601": "避免使用 shell=True",
        "B608": "避免 SQL 注入",
        ...
    }
    return suggestions.get(test_id, "请参考 Bandit 文档")
```

**覆盖的安全问题**:

| 类别 | 示例规则 | 严重程度 |
|------|---------|---------|
| 密钥泄露 | B105/B106/B107 | ERROR |
| 不安全序列化 | B301/B302 | WARNING |
| 弱加密 | B303/B304/B305 | WARNING |
| XML 攻击 | B307/B313-B320 | WARNING |
| 命令注入 | B601-B607 | ERROR |
| SQL 注入 | B608/B610/B611 | ERROR |
| 模板注入 | B701/B702/B703 | ERROR |

### 3.7 第三层规则: 业务规则

**文件**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/hooks/lib/rules/layer3_business.py`

第三层规则支持三种 Handler 类型:

```
┌─────────────────────────────────────────────────────────────┐
│                  Layer 3 Handler 类型                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Command Handler (静态检查)                                 │
│  ├── 使用正则表达式、AST 解析                               │
│  ├── 速度快，确定性高                                       │
│  └── 示例: ModuleIsolationRule                             │
│                                                             │
│  Prompt Handler (语义判断)                                  │
│  ├── 调用 Haiku 模型进行语义分析                            │
│  ├── 能处理复杂的语义场景                                   │
│  └── 示例: I18nRule, LoggerRule                            │
│                                                             │
│  Agent Handler (深度验证)                                   │
│  ├── spawn 子 Agent 进行深度验证                            │
│  ├── 最强大但开销最大                                       │
│  └── 示例: InterfaceProtectionRule                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3.7.1 ModuleIsolationRule (Command Handler)

```python
class ModuleIsolationRule(Layer3Rule):
    """模块隔离规则 - Command Handler"""

    name = "module_isolation"
    handler_type = "command"
    description = "检查模块间 import 是否符合隔离规则"

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """
        config:
          allowed_imports: ["src.core", "src.utils"]
          forbidden_imports: ["src.internal"]
        """
        # 提取所有 import 语句
        import_pattern = r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))'
        for line_num, line in enumerate(content.split('\n'), 1):
            match = re.match(import_pattern, line.strip())
            if match:
                module = match.group(1) or match.group(2)

                # 检查是否在禁止列表中
                for forbidden in forbidden_imports:
                    if module.startswith(forbidden):
                        violations.append(RuleViolation(
                            severity=Severity.MAJOR,
                            message=f"禁止导入模块 '{module}'",
                            ...
                        ))
```

#### 3.7.2 I18nRule (Prompt Handler)

```python
class I18nRule(Layer3Rule):
    """国际化规则 - Prompt Handler"""

    name = "i18n_required"
    handler_type = "prompt"
    description = "检查 UI 代码是否使用 i18n"

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """
        config:
          target_dirs: ["src/ui/", "src/views/"]
          exclude_patterns: ["test_*", "*_test.py"]
          i18n_function: "_t"
        """
        # 检查文件是否在目标目录中
        if not any(file_path.startswith(d) for d in target_dirs):
            return violations

        # 简化实现: 检测字符串字面量
        # (实际应该调用 Haiku)
        string_pattern = r'["\']([^"\']{10,})["\']'
        for line_num, line in enumerate(content.split('\n'), 1):
            if i18n_function not in line:
                # 简单启发式: 包含空格的长字符串可能是用户可见文本
                if ' ' in string_content and len(string_content) > 15:
                    violations.append(RuleViolation(
                        severity=Severity.MINOR,
                        message=f"可能存在硬编码的用户可见字符串",
                        ...
                    ))
```

**注意**: 当前实现使用正则作为 fallback，实际设计中应该调用 Haiku 模型

#### 3.7.3 InterfaceProtectionRule (Agent Handler)

```python
class InterfaceProtectionRule(Layer3Rule):
    """接口保护规则 - Agent Handler"""

    name = "interface_protection"
    handler_type = "agent"
    description = "检查 Protected Interface 签名是否被修改"

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """
        config:
          protected_files: ["src/core/interfaces.py"]
          protected_functions: ["authenticate", "authorize"]
          protected_classes: ["UserService"]
        """
        # 简化实现: 使用 AST 检测函数签名
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in protected_functions:
                    violations.append(RuleViolation(
                        severity=Severity.CRITICAL,
                        message=f"Protected Function '{node.name}' 被修改",
                        suggestion="修改 Protected Interface 前必须在 plan.md 中声明"
                    ))
```

#### 3.7.4 DynamicRuleLoader (动态规则加载)

```python
class DynamicRuleLoader:
    """从 plan.md 动态加载第三层规则"""

    RULE_REGISTRY = {
        "module_isolation": ModuleIsolationRule,
        "i18n_required": I18nRule,
        "logger_standard": LoggerRule,
        "interface_protection": InterfaceProtectionRule,
    }

    def load_from_plan(self, plan_path: str) -> List[Layer3Rule]:
        """从 plan.md 的 YAML Frontmatter 读取 custom_rules"""
        # 提取 YAML Frontmatter
        parts = content.split('---', 2)
        frontmatter = yaml.safe_load(parts[1])

        # 实例化规则
        rules = []
        for rule_config in frontmatter['custom_rules']:
            rule_name = rule_config.get('rule')
            config = rule_config.get('config', {})
            if rule_name in self.RULE_REGISTRY:
                rules.append(self.RULE_REGISTRY[rule_name](config))

        return rules
```

**plan.md 中的配置示例**:

```markdown
---
custom_rules:
  - rule: module_isolation
    config:
      allowed_imports: ["src.core", "src.utils"]
      forbidden_imports: ["src.internal"]
  - rule: i18n_required
    config:
      target_dirs: ["src/ui/"]
      i18n_function: "_t"
---
```

### 3.8 工具函数

**文件**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/hooks/lib/utils.py`

```python
def create_temp_file(content: str, suffix: str = ".tmp") -> str:
    """创建临时文件并写入内容"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path


def detect_language(file_path: str) -> Optional[str]:
    """根据文件扩展名检测语言"""
    ext = Path(file_path).suffix.lower()
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ...
    }
    return language_map.get(ext)
```

### 3.9 多语言支持模块 (multilang)

**目录**: `/Volumes/Under_M2/a056cw/cw_N0mosAi/.claude/hooks/lib/multilang/`

multilang 模块是 Linter 系统的多语言基础设施层，提供语言检测、AST 解析和分语言规则集管理。

```
┌─────────────────────────────────────────────────────────────┐
│                   multilang 模块架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐        │
│  │  LanguageDetector   │───▶│  TreeSitterEngine   │        │
│  │   语言自动检测       │    │   AST 解析引擎       │        │
│  └─────────────────────┘    └─────────────────────┘        │
│           │                          │                      │
│           ▼                          ▼                      │
│  ┌─────────────────────────────────────────────────┐       │
│  │                LanguageRuleSet                   │       │
│  │  ┌───────────┬───────────┬───────────┬───────┐  │       │
│  │  │ Python    │ JS/TS     │ Go        │ Java  │  │       │
│  │  │ RuleSet   │ RuleSet   │ RuleSet   │RuleSet│  │       │
│  │  │ (ruff)    │ (eslint)  │(golangci) │(check)│  │       │
│  │  └───────────┴───────────┴───────────┴───────┘  │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3.9.1 LanguageDetector (语言检测器)

**文件**: `multilang/language_detector.py`

```python
class Language(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    UNKNOWN = "unknown"


class LanguageDetector:
    """基于文件扩展名的语言自动检测器"""

    def __init__(self, config_path: Optional[Path] = None):
        """初始化语言检测器

        Args:
            config_path: 可选的配置文件路径 (.claude/rules/languages.yml)
        """
        self._ext_map = dict(DEFAULT_EXTENSION_MAP)
        if config_path and config_path.exists():
            self._load_config(config_path)

    def detect(self, file_path: Path) -> Language:
        """检测文件的编程语言"""
        return self._ext_map.get(file_path.suffix, Language.UNKNOWN)
```

**扩展名映射**:

| 扩展名 | 语言 |
|--------|------|
| `.py`, `.pyi` | Python |
| `.js`, `.jsx` | JavaScript |
| `.ts`, `.tsx` | TypeScript |
| `.go` | Go |
| `.java` | Java |

#### 3.9.2 TreeSitterEngine (AST 解析引擎)

**文件**: `multilang/tree_sitter_engine.py`

提供统一的 AST 抽象层，支持跨语言的函数签名提取、导入分析和调用链追踪。

```python
@dataclass
class UnifiedAST:
    """统一 AST 抽象 — 跨语言通用结构"""
    language: Language
    functions: List[FunctionSignature] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    call_sites: List[CallSite] = field(default_factory=list)


class TreeSitterEngine:
    """Tree-sitter 多语言解析引擎

    注意: 此实现需要 tree-sitter 和对应语言的绑定
    如果未安装，将优雅降级到基础 AST 解析
    """

    def parse(self, source: bytes, language: Language) -> UnifiedAST:
        """解析源代码，返回统一 AST"""
        if not self._tree_sitter_available:
            return self._fallback_parse(source, language)
        # Tree-sitter 解析逻辑...

    def _fallback_parse(self, source: bytes, language: Language) -> UnifiedAST:
        """降级解析 - 使用 Python 内置 ast 模块"""
        if language == Language.PYTHON:
            return self._parse_python_fallback(source)
        return UnifiedAST(language=language)
```

**核心数据结构**:

```python
@dataclass
class FunctionSignature:
    """函数签名"""
    name: str
    params: List[str]
    return_type: Optional[str]
    line_number: int


@dataclass
class ImportInfo:
    """导入信息"""
    module: str
    names: List[str]
    is_relative: bool
    line_number: int


@dataclass
class CallSite:
    """调用点"""
    caller: str
    callee: str
    line_number: int
```

#### 3.9.3 LanguageRuleSet (分语言规则集)

**文件**: `multilang/rulesets.py`

为不同编程语言提供专门的 Linter 规则集。

```python
class PythonRuleSet(LanguageRuleSet):
    """Python 规则集: ruff + bandit"""

    def run(self, file_path: Path) -> List[LintResult]:
        """运行 Python Linter"""
        result = subprocess.run(
            ['ruff', 'check', '--output-format=json', str(file_path)],
            capture_output=True, text=True, timeout=30
        )
        # 解析 JSON 输出...


class JSTypeScriptRuleSet(LanguageRuleSet):
    """JS/TS 规则集: eslint + semgrep"""

    def run(self, file_path: Path) -> List[LintResult]:
        """运行 JS/TS Linter"""
        result = subprocess.run(
            ['eslint', '--format=json', str(file_path)],
            capture_output=True, text=True, timeout=30
        )
        # 解析 JSON 输出...
```

**规则集注册表**:

```python
RULESET_REGISTRY = {
    Language.PYTHON: PythonRuleSet,
    Language.JAVASCRIPT: JSTypeScriptRuleSet,
    Language.TYPESCRIPT: lambda: JSTypeScriptRuleSet(Language.TYPESCRIPT),
    Language.GO: GoRuleSet,
    Language.JAVA: JavaRuleSet,
}
```

#### 3.9.4 multilang 与 Linter 系统的关系

```
┌─────────────────────────────────────────────────────────────────┐
│                    Linter 系统调用关系                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  AgentLinterEngine.run()                                        │
│       │                                                          │
│       ├─▶ utils.detect_language()      ← 基础检测               │
│       │         │                                               │
│       │         └─▶ 或使用 multilang.LanguageDetector           │
│       │                    (更完整的语言检测)                    │
│       │                                                          │
│       ├─▶ Layer1 语法规则                                       │
│       │         │                                               │
│       │         ├─▶ RuffRule (Python)                          │
│       │         │         │                                     │
│       │         │         └─▶ 可调用 PythonRuleSet              │
│       │         │                                               │
│       │         └─▶ ESLintRule (JS/TS)                         │
│       │                   │                                     │
│       │                   └─▶ 可调用 JSTypeScriptRuleSet        │
│       │                                                          │
│       └─▶ Layer3 业务规则                                       │
│                 │                                               │
│                 └─▶ ModuleIsolationRule 等                      │
│                           │                                     │
│                           └─▶ 可使用 TreeSitterEngine           │
│                                      提取 imports 进行检查       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**关键说明**:

| 问题 | 答案 |
|------|------|
| **multilang 是否用于语法检查?** | ✅ 是的，但作为独立模块存在 |
| **与 layer1_syntax.py 的关系?** | 平行关系，可互相调用 |
| **当前集成状态** | 模块已实现，但 Linter Engine 未直接引用 |
| **设计意图** | 为未来多语言扩展提供基础设施 |

#### 3.9.5 使用示例

```python
from lib.multilang import LanguageDetector, TreeSitterEngine, get_ruleset

# 语言检测
detector = LanguageDetector()
language = detector.detect(Path("src/auth/service.py"))
# → Language.PYTHON

# AST 解析
engine = TreeSitterEngine()
with open("src/auth/service.py", "rb") as f:
    ast = engine.parse(f.read(), Language.PYTHON)

# 提取函数签名
functions = engine.extract_functions(ast)
for func in functions:
    print(f"{func.name}({', '.join(func.params)}) -> {func.return_type}")

# 使用分语言规则集
ruleset = get_ruleset(Language.PYTHON)
results = ruleset.run(Path("src/auth/service.py"))
for r in results:
    print(f"[{r.severity}] {r.rule_id}: {r.message} (line {r.line_number})")
```

---

## 4. 设计 vs 实现对比

### 4.1 完成度分析

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
│  ├── ModuleIsolationRule       ✅ Command Handler 实现      │
│  ├── I18nRule                  ⚠️ 简化实现 (未调用 Haiku)   │
│  ├── LoggerRule                ✅ Command Handler 实现      │
│  ├── InterfaceProtectionRule   ⚠️ 简化实现 (未比对签名)     │
│  └── DynamicRuleLoader         ✅ 基本实现                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 差异分析

| 组件 | 设计要求 | 实际实现 | 差距 |
|------|---------|---------|------|
| **Prompt Handler** | 调用 Haiku 进行语义分析 | 使用正则 fallback | 未集成 AI 能力 |
| **Agent Handler** | spawn 子 Agent 深度验证 | 仅 AST 静态检查 | 未实现 Agent 机制 |
| **签名比对** | 与历史签名对比 | 仅检测存在性 | 缺少持久化比对 |
| **配置来源** | plan.md + YAML 文件 | 仅 plan.md | 未支持独立配置文件 |

### 4.3 接口差异

**架构文档设计**:

```python
class BaseRule:
    def check(self, code, context) -> RuleResult:
        pass

class AgentLinterEngine:
    def run_all_rules(self, code, layer) -> List[RuleResult]:
        pass
```

**实际实现**:

```python
class BaseRule:
    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        pass

class AgentLinterEngine:
    def run(self, file_path: str, content: str, layers: Optional[List[int]] = None) -> LinterResult:
        pass
```

**差异说明**:

1. `check()` 参数从 `(code, context)` 改为 `(file_path, content)`
2. 返回类型从 `RuleResult` 改为 `List[RuleViolation]`
3. 引擎方法名从 `run_all_rules()` 改为 `run()`

---

## 5. 使用示例

### 5.1 基本使用

```python
from lib.linter_engine import AgentLinterEngine
from lib.rules.layer1_syntax import RuffRule, ESLintRule
from lib.rules.layer2_security import BanditRule
from lib.rules.layer3_business import ModuleIsolationRule

# 创建引擎
engine = AgentLinterEngine()

# 注册规则
engine.register_rule(RuffRule())
engine.register_rule(ESLintRule())
engine.register_rule(BanditRule())
engine.register_rule(ModuleIsolationRule({
    "allowed_imports": ["src.core", "src.utils"],
    "forbidden_imports": ["src.internal"]
}))

# 运行检查
result = engine.run("src/auth/service.py", python_code)

if result.passed:
    print("✅ 检查通过")
else:
    print(f"❌ 发现 {len(result.violations)} 个问题")
    for v in result.violations:
        print(f"  [{v.severity.value}] {v.rule}: {v.message} (line {v.line})")
```

### 5.2 按层级过滤

```python
# 只运行 Layer 1 (语法检查)
result = engine.run("src/auth/service.py", content, layers=[1])

# 只运行 Layer 2 和 Layer 3
result = engine.run("src/auth/service.py", content, layers=[2, 3])
```

### 5.3 动态加载规则

```python
from lib.rules.layer3_business import DynamicRuleLoader

loader = DynamicRuleLoader()

# 从 plan.md 加载规则
rules = loader.load_from_plan("tasks/t1-feature/plan.md")

# 注册到引擎
for rule in rules:
    engine.register_rule(rule)
```

### 5.4 结果序列化

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

## 6. 扩展指南

### 6.1 添加新的语法规则 (Layer 1)

**步骤 1**: 创建规则类

```python
# .claude/hooks/lib/rules/layer1_syntax.py

class GolangCILintRule(BaseRule):
    """golangci-lint Go Linter 封装"""

    name = "golangci-lint"
    layer = 1
    description = "Go 语法和风格检查 (golangci-lint)"
    supported_languages = ["go"]

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        violations = []

        # 检查工具是否可用
        try:
            subprocess.run(["golangci-lint", "version"],
                          capture_output=True, check=True)
        except FileNotFoundError:
            return [RuleViolation(
                rule="golangci-lint:not_found",
                message="golangci-lint 未安装",
                line=0, column=0,
                severity=Severity.WARNING,
                suggestion="go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest",
                source="layer1"
            )]

        # 写入临时文件并执行
        temp_file = create_temp_file(content, suffix=".go")
        try:
            result = subprocess.run(
                ["golangci-lint", "run", "--output-format=json", temp_file],
                capture_output=True, text=True
            )
            # 解析输出...
        finally:
            os.remove(temp_file)

        return violations
```

**步骤 2**: 注册规则

```python
engine.register_rule(GolangCILintRule())
```

### 6.2 添加新的业务规则 (Layer 3)

**步骤 1**: 创建规则类

```python
# .claude/hooks/lib/rules/layer3_business.py

class TraceIdRule(Layer3Rule):
    """Trace ID 传递规则 - Prompt Handler"""

    name = "trace_id_required"
    handler_type = "prompt"
    description = "检查 trace_id 是否正确传递"
    layer = 3

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        violations = []
        config = self.config or {}

        # 检测函数调用是否传递 trace_id
        # 示例: 检测 service 层调用是否带 trace_id 参数

        service_pattern = r'(\w+)\.(\w+)\([^)]*\)'
        for line_num, line in enumerate(content.split('\n'), 1):
            matches = re.finditer(service_pattern, line)
            for match in matches:
                args = match.group(0)
                if 'trace_id' not in args and 'traceId' not in args:
                    violations.append(RuleViolation(
                        rule_name=self.name,
                        severity=Severity.MINOR,
                        file_path=file_path,
                        line_number=line_num,
                        message=f"调用 {match.group(2)} 未传递 trace_id",
                        suggestion="确保所有服务调用都传递 trace_id 参数"
                    ))

        return violations
```

**步骤 2**: 注册到 DynamicRuleLoader

```python
class DynamicRuleLoader:
    RULE_REGISTRY = {
        "module_isolation": ModuleIsolationRule,
        "i18n_required": I18nRule,
        "logger_standard": LoggerRule,
        "interface_protection": InterfaceProtectionRule,
        "trace_id_required": TraceIdRule,  # 新增
    }
```

**步骤 3**: 在 plan.md 中使用

```markdown
---
custom_rules:
  - rule: trace_id_required
    config:
      service_modules: ["src/services/", "src/api/"]
---
```

### 6.3 扩展建议

1. **实现 Prompt Handler 的 AI 集成**
   - 接入 Haiku 模型进行语义分析
   - 设计 prompt 模板用于 i18n 检测等场景

2. **实现 Agent Handler 的子 Agent 机制**
   - 设计 Agent spawn 接口
   - 实现签名持久化和比对

3. **支持独立配置文件**
   - 添加 `.nomos/linter.yaml` 配置支持
   - 合并 plan.md 和配置文件的规则

4. **增量检查**
   - 基于文件 hash 的缓存机制
   - 只检查变更的文件

---

## 7. 总结

N0mosAi Linter 系统通过三层规则体系，实现了从语法到业务的全面代码审查。核心特点包括:

1. **前置审查**: 在代码写入前拦截问题
2. **三层防护**: Layer 1 (语法) → Layer 2 (安全) → Layer 3 (业务)
3. **可扩展**: 基于基类的设计便于添加新规则
4. **动态配置**: 支持从 plan.md 加载项目特定规则

当前实现完成了核心框架和大部分规则，Prompt Handler 和 Agent Handler 的 AI 能力集成是后续优化的重点方向。

---

*文档版本: 1.0*
*最后更新: 2026-02-27*
*来源: N0mosAi 系统架构与代码分析*
