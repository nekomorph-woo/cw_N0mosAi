"""
语言自动检测器 (Language Detector)

基于文件扩展名自动检测编程语言类型
"""

from pathlib import Path
from enum import Enum
from typing import Optional, Dict
import yaml


class Language(Enum):
    """支持的编程语言"""
    # Tier 1: 原生工具 (高精度)
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    # Tier 2: Tree-sitter (广覆盖)
    GO = "go"
    JAVA = "java"
    RUST = "rust"
    C = "c"
    CPP = "cpp"
    CSHARP = "c_sharp"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    LUA = "lua"
    PERL = "perl"
    R = "r"
    # 其他
    UNKNOWN = "unknown"


# 默认扩展名映射
DEFAULT_EXTENSION_MAP: Dict[str, Language] = {
    # Tier 1: 原生工具
    ".py": Language.PYTHON,
    ".pyi": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".mts": Language.TYPESCRIPT,
    ".cts": Language.TYPESCRIPT,
    # Tier 2: Tree-sitter
    ".go": Language.GO,
    ".java": Language.JAVA,
    ".rs": Language.RUST,
    ".c": Language.C,
    ".h": Language.C,
    ".cpp": Language.CPP,
    ".cc": Language.CPP,
    ".cxx": Language.CPP,
    ".hpp": Language.CPP,
    ".hxx": Language.CPP,
    ".cs": Language.CSHARP,
    ".rb": Language.RUBY,
    ".php": Language.PHP,
    ".swift": Language.SWIFT,
    ".kt": Language.KOTLIN,
    ".kts": Language.KOTLIN,
    ".scala": Language.SCALA,
    ".lua": Language.LUA,
    ".pl": Language.PERL,
    ".pm": Language.PERL,
    ".r": Language.R,
    ".R": Language.R,
}

# Tier 1 语言 (使用原生 linter)
TIER1_LANGUAGES = {Language.PYTHON, Language.JAVASCRIPT, Language.TYPESCRIPT}


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
        """检测文件的编程语言

        Args:
            file_path: 文件路径

        Returns:
            Language 枚举值
        """
        return self._ext_map.get(file_path.suffix, Language.UNKNOWN)

    def is_tier1(self, language: Language) -> bool:
        """检查是否为 Tier 1 语言 (使用原生 linter)

        Args:
            language: 语言枚举

        Returns:
            是否为 Tier 1
        """
        return language in TIER1_LANGUAGES

    def get_linter_tier(self, language: Language) -> int:
        """获取语言对应的 linter 层级

        Args:
            language: 语言枚举

        Returns:
            1 = 原生工具, 2 = Tree-sitter, 0 = 不支持
        """
        if language in TIER1_LANGUAGES:
            return 1
        elif language != Language.UNKNOWN:
            return 2
        return 0

    def _load_config(self, config_path: Path) -> None:
        """从 languages.yml 加载自定义映射

        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config or 'extensions' not in config:
                return

            # 覆盖默认映射
            for ext, lang_str in config['extensions'].items():
                try:
                    lang = Language(lang_str.lower())
                    self._ext_map[ext] = lang
                except ValueError:
                    # 忽略无效的语言值
                    pass

        except (yaml.YAMLError, OSError):
            # 配置文件加载失败，使用默认配置
            pass
