"""
AgentLinterEngine 核心引擎
"""

from typing import List, Optional
from .rules.base_rule import BaseRule, LinterResult, RuleViolation, Severity
from .utils import detect_language


class AgentLinterEngine:
    """核心 Linter 引擎"""

    def __init__(self):
        self.rules: List[BaseRule] = []

    def register_rule(self, rule: BaseRule) -> None:
        """注册规则"""
        self.rules.append(rule)

    def run(self, file_path: str, content: str,
            layers: Optional[List[int]] = None) -> LinterResult:
        """
        运行 Linter 检查

        Args:
            file_path: 文件路径
            content: 文件内容
            layers: 指定运行的层级 (None=全部)

        Returns:
            LinterResult
        """
        # 检测语言
        language = self._detect_language(file_path)
        if not language:
            # 非代码文件，直接通过
            return LinterResult(
                passed=True,
                file_path=file_path,
                summary="非代码文件，跳过检查"
            )

        # 过滤适用的规则
        applicable_rules = self._filter_rules(language, layers)

        # 执行所有规则
        all_violations = []
        for rule in applicable_rules:
            try:
                violations = rule.check(file_path, content)
                all_violations.extend(violations)
            except Exception as e:
                # 规则执行失败，记录为警告
                all_violations.append(RuleViolation(
                    rule=f"{rule.name}:error",
                    message=f"规则执行失败: {str(e)}",
                    line=0,
                    column=0,
                    severity=Severity.WARNING,
                    suggestion="检查规则配置或工具安装",
                    source=f"layer{rule.layer}"
                ))

        # 判断是否通过（只有 ERROR 才算失败）
        errors = [v for v in all_violations if v.severity == Severity.ERROR]
        passed = len(errors) == 0

        # 生成摘要
        summary = self._generate_summary(all_violations)

        return LinterResult(
            passed=passed,
            file_path=file_path,
            violations=all_violations,
            summary=summary
        )

    def _detect_language(self, file_path: str) -> Optional[str]:
        """根据文件扩展名检测语言"""
        return detect_language(file_path)

    def _filter_rules(self, language: str,
                      layers: Optional[List[int]]) -> List[BaseRule]:
        """过滤适用的规则"""
        filtered = []

        for rule in self.rules:
            # 检查层级
            if layers is not None and rule.layer not in layers:
                continue

            # 检查语言适用性
            if not rule.is_applicable(language):
                continue

            filtered.append(rule)

        return filtered

    def _generate_summary(self, violations: List[RuleViolation]) -> str:
        """生成摘要"""
        if not violations:
            return "✅ 所有检查通过"

        error_count = sum(1 for v in violations if v.severity == Severity.ERROR)
        warning_count = sum(1 for v in violations if v.severity == Severity.WARNING)
        info_count = sum(1 for v in violations if v.severity == Severity.INFO)

        parts = []
        if error_count > 0:
            parts.append(f"{error_count} error")
        if warning_count > 0:
            parts.append(f"{warning_count} warning")
        if info_count > 0:
            parts.append(f"{info_count} info")

        return f"发现 {len(violations)} 个问题 ({', '.join(parts)})"
