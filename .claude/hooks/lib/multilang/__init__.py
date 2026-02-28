"""
多语言支持模块

提供跨语言的 AST 解析、语言检测和规则集管理
"""

from .language_detector import (
    Language,
    LanguageDetector,
    DEFAULT_EXTENSION_MAP,
    TIER1_LANGUAGES
)
from .tree_sitter_engine import (
    TreeSitterEngine,
    UnifiedAST,
    FunctionSignature,
    ImportInfo,
    CallSite,
    SyntaxError
)
from .rulesets import (
    LanguageRuleSet,
    LintResult,
    PythonRuleSet,
    JSTypeScriptRuleSet,
    GoRuleSet,
    JavaRuleSet,
    get_ruleset,
    RULESET_REGISTRY
)

__all__ = [
    # Language Detection
    'Language',
    'LanguageDetector',
    'DEFAULT_EXTENSION_MAP',
    'TIER1_LANGUAGES',
    # Tree-sitter Engine
    'TreeSitterEngine',
    'UnifiedAST',
    'FunctionSignature',
    'ImportInfo',
    'CallSite',
    'SyntaxError',
    # Rulesets
    'LanguageRuleSet',
    'LintResult',
    'PythonRuleSet',
    'JSTypeScriptRuleSet',
    'GoRuleSet',
    'JavaRuleSet',
    'get_ruleset',
    'RULESET_REGISTRY',
]
