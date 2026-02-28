"""
l3_foundation - Layer 3 基础能力层

动态规则系统的核心基础设施

导出清单:
  - DynamicRule: 动态规则基类 (Layer 3 专用)
  - DynamicViolation: 动态规则违规记录
  - Severity: 严重程度
  - AIClient: AI 调用客户端
  - ASTUtils: AST 解析工具
  - PromptBuilder: Prompt 构建器
  - RuleContext: 规则上下文
  - DynamicRuleLoader: 动态规则加载器
"""

from .dynamic_rule import DynamicRule, DynamicViolation, Severity

# 向后兼容别名
RuleViolation = DynamicViolation
BaseRule = DynamicRule  # 保持与旧代码的兼容性
from .ai_client import AIClient
from .ast_utils import ASTUtils
from .prompt_builder import PromptBuilder, PromptTemplate
from .rule_context import RuleContext
from .rule_loader import DynamicRuleLoader, load_rules_from_task, SecurityError
from .rule_generator import RuleGenerator, RuleSyncer, RuleSpec, generate_rules_from_plan

__all__ = [
    "DynamicRule",
    "BaseRule",  # 别名，向后兼容
    "DynamicViolation",
    "RuleViolation",  # 别名，向后兼容
    "Severity",
    "AIClient",
    "ASTUtils",
    "PromptBuilder",
    "PromptTemplate",
    "RuleContext",
    "DynamicRuleLoader",
    "load_rules_from_task",
    "SecurityError",
    "RuleGenerator",
    "RuleSyncer",
    "RuleSpec",
    "generate_rules_from_plan",
]

__version__ = "1.0.0"
