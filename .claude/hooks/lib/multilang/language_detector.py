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
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    UNKNOWN = "unknown"


# 默认扩展名映射
DEFAULT_EXTENSION_MAP: Dict[str, Language] = {
    ".py": Language.PYTHON,
    ".pyi": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".go": Language.GO,
    ".java": Language.JAVA,
}


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
