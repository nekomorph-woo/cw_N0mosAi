"""
Linter 规则基类和数据结构
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


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

    def to_json(self) -> dict:
        """转换为 JSON 格式"""
        return {
            "passed": self.passed,
            "file_path": self.file_path,
            "violation_count": len(self.violations),
            "violations": [
                {
                    "rule": v.rule,
                    "message": v.message,
                    "line": v.line,
                    "column": v.column,
                    "severity": v.severity.value,
                    "suggestion": v.suggestion,
                    "source": v.source
                }
                for v in self.violations
            ],
            "summary": self.summary
        }


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

        Args:
            language: 语言名称

        Returns:
            是否适用
        """
        if not self.supported_languages:
            return True  # 如果未指定语言，则适用于所有语言
        return language in self.supported_languages
