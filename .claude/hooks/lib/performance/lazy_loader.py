"""
按需加载器 (Lazy Loader)

只加载当前语言需要的规则集，降低内存占用
"""

import importlib
from typing import Dict, Any, Optional


class LazyRuleSetLoader:
    """按需加载规则集 — 只加载当前语言需要的规则"""

    _loaded: Dict[str, Any] = {}

    @classmethod
    def load(cls, language: str) -> Optional[Any]:
        """加载指定语言的规则集

        Args:
            language: 语言名称 (如 "python", "javascript")

        Returns:
            规则集实例，如果加载失败返回 None
        """
        if language in cls._loaded:
            return cls._loaded[language]

        ruleset = cls._import_ruleset(language)
        if ruleset:
            cls._loaded[language] = ruleset

        return ruleset

    @classmethod
    def _import_ruleset(cls, language: str) -> Optional[Any]:
        """动态导入对应语言的规则集模块

        Args:
            language: 语言名称

        Returns:
            规则集实例，如果导入失败返回 None
        """
        try:
            # 尝试从 multilang.rulesets 导入
            from ..multilang.rulesets import get_ruleset
            from ..multilang.language_detector import Language

            # 将字符串转换为 Language 枚举
            lang_enum = Language(language.lower())
            return get_ruleset(lang_enum)

        except (ImportError, ValueError, AttributeError):
            return None

    @classmethod
    def clear(cls) -> None:
        """清空已加载的规则集"""
        cls._loaded.clear()

    @classmethod
    def is_loaded(cls, language: str) -> bool:
        """检查规则集是否已加载

        Args:
            language: 语言名称

        Returns:
            是否已加载
        """
        return language in cls._loaded
