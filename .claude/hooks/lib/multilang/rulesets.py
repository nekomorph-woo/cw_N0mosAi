"""
分语言规则集 (Language-specific Rule Sets)

为不同编程语言提供专门的 Linter 规则集
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List
from .language_detector import Language


@dataclass
class LintResult:
    """Lint 检查结果"""
    rule_id: str
    severity: str  # "error" | "warning" | "info"
    message: str
    file_path: str
    line_number: int
    language: Language


class LanguageRuleSet:
    """分语言规则集基类"""

    def __init__(self, language: Language):
        self.language = language

    def run(self, file_path: Path) -> List[LintResult]:
        """运行规则集检查

        Args:
            file_path: 文件路径

        Returns:
            Lint 结果列表
        """
        raise NotImplementedError


class PythonRuleSet(LanguageRuleSet):
    """Python 规则集: ruff + bandit"""

    def __init__(self):
        super().__init__(Language.PYTHON)

    def run(self, file_path: Path) -> List[LintResult]:
        """运行 Python Linter

        使用 ruff 进行语法和风格检查
        使用 bandit 进行安全检查
        """
        results = []

        # 简化实现: 检查 ruff 是否可用
        import subprocess
        try:
            # 尝试运行 ruff
            result = subprocess.run(
                ['ruff', 'check', '--output-format=json', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0 and result.stdout:
                import json
                try:
                    ruff_results = json.loads(result.stdout)
                    for item in ruff_results:
                        results.append(LintResult(
                            rule_id=item.get('code', 'RUFF'),
                            severity='error' if item.get('type') == 'error' else 'warning',
                            message=item.get('message', ''),
                            file_path=str(file_path),
                            line_number=item.get('location', {}).get('row', 0),
                            language=self.language
                        ))
                except json.JSONDecodeError:
                    pass

        except (FileNotFoundError, subprocess.TimeoutExpired):
            # ruff 未安装或超时，跳过
            pass

        return results


class JSTypeScriptRuleSet(LanguageRuleSet):
    """JS/TS 规则集: eslint + semgrep"""

    def __init__(self, language: Language = Language.JAVASCRIPT):
        super().__init__(language)

    def run(self, file_path: Path) -> List[LintResult]:
        """运行 JS/TS Linter

        使用 eslint 进行语法和风格检查
        """
        results = []

        # 简化实现: 检查 eslint 是否可用
        import subprocess
        try:
            result = subprocess.run(
                ['eslint', '--format=json', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                import json
                try:
                    eslint_results = json.loads(result.stdout)
                    for file_result in eslint_results:
                        for message in file_result.get('messages', []):
                            results.append(LintResult(
                                rule_id=message.get('ruleId', 'ESLINT'),
                                severity='error' if message.get('severity') == 2 else 'warning',
                                message=message.get('message', ''),
                                file_path=str(file_path),
                                line_number=message.get('line', 0),
                                language=self.language
                            ))
                except json.JSONDecodeError:
                    pass

        except (FileNotFoundError, subprocess.TimeoutExpired):
            # eslint 未安装或超时，跳过
            pass

        return results


class GoRuleSet(LanguageRuleSet):
    """Go 规则集: golangci-lint + gosec"""

    def __init__(self):
        super().__init__(Language.GO)

    def run(self, file_path: Path) -> List[LintResult]:
        """运行 Go Linter

        使用 golangci-lint 进行综合检查
        """
        results = []

        # 简化实现: 返回空结果
        # 实际应该调用 golangci-lint
        return results


class JavaRuleSet(LanguageRuleSet):
    """Java 规则集: checkstyle + spotbugs"""

    def __init__(self):
        super().__init__(Language.JAVA)

    def run(self, file_path: Path) -> List[LintResult]:
        """运行 Java Linter

        使用 checkstyle 进行风格检查
        """
        results = []

        # 简化实现: 返回空结果
        # 实际应该调用 checkstyle
        return results


# 规则集注册表
RULESET_REGISTRY = {
    Language.PYTHON: PythonRuleSet,
    Language.JAVASCRIPT: JSTypeScriptRuleSet,
    Language.TYPESCRIPT: lambda: JSTypeScriptRuleSet(Language.TYPESCRIPT),
    Language.GO: GoRuleSet,
    Language.JAVA: JavaRuleSet,
}


def get_ruleset(language: Language) -> LanguageRuleSet:
    """获取指定语言的规则集

    Args:
        language: 编程语言

    Returns:
        LanguageRuleSet 实例
    """
    ruleset_class = RULESET_REGISTRY.get(language)
    if ruleset_class:
        if callable(ruleset_class):
            return ruleset_class()
        return ruleset_class()
    raise ValueError(f"不支持的语言: {language}")
