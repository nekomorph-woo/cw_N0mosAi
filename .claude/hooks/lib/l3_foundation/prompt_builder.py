"""
Prompt 构建模块 - 提供 Prompt 构建能力

l3_foundation 基础能力层核心模块
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


class PromptTemplate:
    """Prompt 模板 - 支持变量替换"""

    def __init__(self, template: str):
        """
        初始化模板

        Args:
            template: 模板字符串，使用 {variable} 语法
        """
        self.template = template

    def render(self, **kwargs) -> str:
        """
        渲染模板

        Args:
            **kwargs: 模板变量

        Returns:
            渲染后的字符串
        """
        return self.template.format(**kwargs)

    @classmethod
    def from_file(cls, file_path: str) -> 'PromptTemplate':
        """
        从文件加载模板

        Args:
            file_path: 模板文件路径

        Returns:
            PromptTemplate 实例
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return cls(f.read())


# 预定义模板
COMMAND_HANDLER_TEMPLATE = """你是 Python 代码生成专家。根据用户的业务规则需求，生成 Layer 3 规则脚本。

## 任务信息

- Task ID: {task_id}
- Task 目录: {task_dir}
- 项目根目录: {project_root}

## 业务规则需求

{rule_description}

## 生成要求

1. **Handler 类型**: Command Handler (使用 AST 静态分析)
2. **脚本模板**: 必须继承 DynamicRule
3. **基础能力**: 必须使用 l3_foundation 提供的能力
   - DynamicRule: 动态规则基类 (Layer 3 专用)
   - DynamicViolation: 动态规则违规记录
   - Severity: 严重程度
   - ASTUtils: AST 解析工具
   - FileMatcher: 文件匹配工具 (用于 should_check)
   - RuleContext: 规则上下文

4. **检查逻辑**:
   - 使用 ASTUtils.parse() 解析代码
   - 使用 ASTUtils.find_functions() / find_classes() 查找目标
   - 实现具体的检查逻辑
   - 返回 DynamicViolation 列表

5. **文件过滤** (should_check):
   - 使用 FileMatcher.match_patterns() 实现文件匹配
   - 支持的 glob 模式: `*.py`, `src/**/*.py`, `*.ts,*.tsx`
   - 如果目标文件为空，则检查所有文件
   - 示例: `FileMatcher.match_patterns(file_path, ["*.py"])`

## 输出格式

直接输出完整的 Python 脚本，不要包含任何解释文字。
"""

PROMPT_HANDLER_TEMPLATE = """你是 Python 代码生成专家。根据用户的业务规则需求，生成 Layer 3 规则脚本。

## 任务信息

- Task ID: {task_id}
- Task 目录: {task_dir}
- 项目根目录: {project_root}

## 业务规则需求

{rule_description}

## 生成要求

1. **Handler 类型**: Prompt Handler (使用 AI 语义分析)
2. **脚本模板**: 必须继承 DynamicRule
3. **基础能力**: 必须使用 l3_foundation 提供的能力
   - DynamicRule: 动态规则基类 (Layer 3 专用)
   - DynamicViolation: 动态规则违规记录
   - Severity: 严重程度
   - AIClient: AI 调用客户端
   - PromptBuilder: Prompt 构建器
   - FileMatcher: 文件匹配工具 (用于 should_check)
   - RuleContext: 规则上下文

4. **检查逻辑**:
   - 实现 _should_ai_check() 快速预检
   - 实现 _build_prompt() 构建 AI prompt
   - 添加 few-shot 示例到 prompt
   - 实现 _parse_ai_result() 解析 AI 返回

5. **文件过滤** (should_check):
   - 使用 FileMatcher.match_patterns() 实现文件匹配
   - 支持的 glob 模式: `*.py`, `src/**/*.py`, `*.ts,*.tsx`

6. **Prompt 设计**:
   - 清晰描述规则要求
   - 提供正反示例
   - 明确输出格式 (JSON)
   - 处理边界情况

## 输出格式

直接输出完整的 Python 脚本，不要包含任何解释文字。
"""
