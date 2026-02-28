"""
基础规则模块 - 定义规则基类和数据结构

l3_foundation 基础能力层核心模块
"""

from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass


class Severity(Enum):
    """违规严重程度"""
    ERROR = "error"      # 阻断性错误
    WARNING = "warning"  # 警告
    INFO = "info"        # 信息提示


@dataclass
class RuleViolation:
    """规则违规记录"""
    rule: str              # 规则名称
    message: str           # 违规描述
    line: int              # 行号
    column: int            # 列号
    severity: Severity     # 严重程度
    suggestion: str = ""   # 修复建议

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "rule": self.rule,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "suggestion": self.suggestion
        }


class BaseRule:
    """规则基类 - 所有规则必须继承此类"""

    # 规则元信息 (子类必须定义)
    name: str = ""              # 规则名称
    layer: int = 3              # 规则层级
    description: str = ""       # 规则描述
    handler_type: str = "command"  # handler 类型: command / prompt

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化规则

        Args:
            config: 规则配置 (从 plan.md 读取)
        """
        self.config = config or {}

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
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
