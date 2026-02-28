"""
动态规则模块 - 定义 Layer 3 动态规则基类和数据结构

l3_foundation 基础能力层核心模块

与 rules/base_rule.py 的区别:
- rules/base_rule.py: Layer 1/2 静态规则 (Ruff, ESLint, Bandit 等)
- dynamic_rule.py: Layer 3 动态规则 (用户自定义业务规则)
"""

import fnmatch
from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass


class Severity(Enum):
    """违规严重程度"""
    ERROR = "error"      # 阻断性错误
    WARNING = "warning"  # 警告
    INFO = "info"        # 信息提示


@dataclass
class DynamicViolation:
    """动态规则违规记录 - Layer 3 专用"""
    rule: str              # 规则名称
    message: str           # 违规描述
    line: int              # 行号
    column: int            # 列号
    severity: Severity     # 严重程度
    suggestion: str = ""   # 修复建议
    source: str = "layer3" # 来源 (layer1/layer2/layer3)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "rule": self.rule,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "suggestion": self.suggestion,
            "source": self.source
        }


class DynamicRule:
    """动态规则基类 - Layer 3 业务规则必须继承此类

    与 BaseRule (rules/base_rule.py) 的区别:
    - BaseRule: 用于 Layer 1/2 静态规则，有 supported_languages, is_applicable()
    - DynamicRule: 用于 Layer 3 动态规则，有 handler_type, config, should_check()
    """

    # 规则元信息 (子类必须定义)
    name: str = ""              # 规则名称
    layer: int = 3              # 规则层级 (固定为 3)
    description: str = ""       # 规则描述
    handler_type: str = "command"  # handler 类型: command / prompt

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化规则

        Args:
            config: 规则配置 (从 plan.md 读取)
        """
        self.config = config or {}

    def check(self, file_path: str, content: str) -> List[DynamicViolation]:
        """
        检查代码是否违规

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            违规记录列表
        """
        raise NotImplementedError("子类必须实现 check() 方法")

    def should_check(self, file_path: str) -> bool:
        """
        判断是否需要检查此文件

        Args:
            file_path: 文件路径

        Returns:
            True 表示需要检查
        """
        # 默认检查所有文件，子类可覆盖
        return True


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

        Args:
            file_path: 文件路径 (如: src/api/user.py)
            patterns: glob 模式列表

        Returns:
            是否匹配任意模式
        """
        import glob as glob_module

        # 规范化路径分隔符
        normalized_path = file_path.replace("\\", "/")

        for pattern in patterns:
            pattern = pattern.strip()
            if not pattern:
                continue

            # 处理逗号分隔的多模式
            if "," in pattern:
                sub_patterns = [p.strip() for p in pattern.split(",")]
                if FileMatcher.match_patterns(file_path, sub_patterns):
                    return True
                continue

            # 规范化模式
            normalized_pattern = pattern.replace("\\", "/")

            # 处理 ** 模式 - 转换为 fnmatch 兼容格式
            if "**" in normalized_pattern:
                # **/* 表示任意深度的子目录
                # 将 src/api/**/*.py 转换为 src/api/*.py (fnmatch 会递归匹配)
                fnmatch_pattern = normalized_pattern.replace("**/", "*")
                # 或者: src/**/*.py -> src/*.py
                if not normalized_pattern.startswith("**"):
                    # 确保路径前缀存在
                    prefix = normalized_pattern.split("**/")[0]
                    suffix = normalized_pattern.split("**/")[-1]
                    # 检查路径是否以 prefix 开头
                    if normalized_path.startswith(prefix.rstrip("/")):
                        # 检查剩余部分是否匹配 suffix
                        remaining = normalized_path[len(prefix.rstrip("/")):]
                        if remaining.startswith("/"):
                            remaining = remaining[1:]
                        if fnmatch.fnmatch(remaining, suffix) or fnmatch.fnmatch(remaining.split("/")[-1], suffix):
                            return True
                    continue
                else:
                    fnmatch_pattern = normalized_pattern.replace("**/", "")

            # fnmatch 匹配
            if fnmatch.fnmatch(normalized_path, normalized_pattern):
                return True

            # 尝试匹配路径的最后一部分 (文件名)
            filename = normalized_path.split("/")[-1]
            if fnmatch.fnmatch(filename, normalized_pattern):
                return True

            # 尝试简化模式: src/api/**/*.py -> src/api/*.py
            if "/**/" in normalized_pattern:
                simple_pattern = normalized_pattern.replace("/**/", "/")
                if fnmatch.fnmatch(normalized_path, simple_pattern):
                    return True

        return False

    @staticmethod
    def match_extensions(file_path: str, extensions: List[str]) -> bool:
        """
        检查文件扩展名是否匹配

        Args:
            file_path: 文件路径
            extensions: 扩展名列表 (如: [".py", ".pyx"])

        Returns:
            是否匹配
        """
        for ext in extensions:
            if file_path.endswith(ext):
                return True
        return False
