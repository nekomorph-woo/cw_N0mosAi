# 规则示例 (Rule Examples)

这个目录包含动态规则系统的示例规则脚本。

## 📁 示例文件

| 示例文件 | Handler 类型 | 说明 |
|---------|-------------|------|
| `module_isolation.py.example` | Command | 模块隔离检查 - 演示如何使用 AST 检查导入语句 |
| `logger_standard.py.example` | Prompt | Logger 规范 - 演示如何使用 AI 语义判断 + 正则降级 |
| `i18n_check.py.example` | Prompt | 国际化检查 - 演示如何检查 UI 文本是否国际化 |
| `interface_protection.py.example` | Command | 接口保护 - 演示如何检查函数/类签名变更 |

## 🎯 如何使用

### 在 plan.md 中引用示例

```markdown
## 业务规则

#### 规则 1: 禁止使用 print 语句

- **描述**: 业务代码中不应使用 print()，应使用 logger
- **参考示例**: logger_standard.py.example
- **Handler**: `command`
- **严重程度**: `warning`
```

### 作为学习参考

这些示例展示了如何实现不同类型的规则：

- **Command Handler**: 使用 `ASTUtils` 进行静态分析
- **Prompt Handler**: 使用 `AIClient` 进行 AI 语义判断

## 📝 示例规则模板

### Command Handler 模板

```python
# 规则元信息
name = "rule_name"
layer = 3
handler_type = "command"
description = "规则描述"

config = {
    # 规则配置参数
}

def check(file_path, content):
    """检查代码是否违规"""
    violations = []

    # 使用 ASTUtils 解析代码
    tree = ASTUtils.parse(content, file_path)

    # 实现检查逻辑...
    # violations.append(RuleViolation(...))  # 或 DynamicViolation(...)

    return violations

def should_check(file_path):
    """判断是否需要检查此文件"""
    return True  # 或根据文件类型/路径判断
```

> **注意**: `RuleViolation` 和 `DynamicViolation` 是同一个类，可以互换使用。

### Prompt Handler 模板

```python
# 规则元信息
name = "rule_name"
layer = 3
handler_type = "prompt"
description = "规则描述"

config = {
    # 规则配置参数
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
    """判断是否需要检查此文件"""
    return True
```

## 💡 可用的基础能力

所有规则脚本都可以使用 l3_foundation 提供的基础能力：

- `DynamicRule`: 动态规则基类 (Layer 3 专用)
  - 别名: `BaseRule` (向后兼容)
- `DynamicViolation`: 动态规则违规记录
  - 别名: `RuleViolation` (向后兼容)
- `Severity`: 严重程度枚举 (ERROR, WARNING, INFO)
- `AIClient`: AI 调用客户端
- `ASTUtils`: AST 解析工具 (多语言支持)
- `PromptBuilder`: Prompt 构建器
- `RuleContext`: 规则上下文

> **注意**: 新代码推荐使用 `DynamicRule` 和 `DynamicViolation`，旧名称 (`BaseRule`, `RuleViolation`) 仍然可用以保持向后兼容。

## 🚀 创建新规则

1. 在 plan.md 中描述业务规则
2. (可选) 参考 `rule_examples/` 中的类似示例
3. 运行规则生成器自动创建规则脚本
4. 在 `task/rules/` 目录中 review 生成的脚本
5. 根据需要修改和调整规则逻辑
