"""
l3_foundation - Layer 3 基础能力层

动态规则系统的核心基础设施

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
from .prompt_builder import PromptBuilder, PromptTemplate
from .rule_context import RuleContext
from .rule_loader import DynamicRuleLoader, load_rules_from_task, SecurityError
from .rule_generator import RuleGenerator, RuleSyncer, RuleSpec, generate_rules_from_plan

__all__ = [
    "BaseRule",
    "RuleViolation",
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
