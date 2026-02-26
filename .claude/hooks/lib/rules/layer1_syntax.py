"""
第一层规则: 语法和风格检查
"""

import subprocess
import json
import os
from typing import List
from .base_rule import BaseRule, RuleViolation, Severity
from ..utils import create_temp_file


class RuffRule(BaseRule):
    """Ruff Python Linter 封装"""

    name = "ruff"
    layer = 1
    description = "Python 语法和风格检查 (Ruff)"
    supported_languages = ["python"]

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """
        调用 ruff check 并解析输出

        实现要点:
        1. 将 content 写入临时文件
        2. 运行 ruff check --output-format=json
        3. 解析 JSON 输出为 RuleViolation 列表
        4. 清理临时文件
        """
        violations = []

        # 检查 ruff 是否可用
        try:
            subprocess.run(["ruff", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return [RuleViolation(
                rule="ruff:not_found",
                message="Ruff 未安装，请运行: pip install ruff",
                line=0,
                column=0,
                severity=Severity.WARNING,
                suggestion="pip install ruff",
                source="layer1"
            )]

        # 写入临时文件
        temp_file = create_temp_file(content, suffix=".py")

        try:
            # 运行 ruff check
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", temp_file],
                capture_output=True,
                text=True
            )

            # 解析 JSON 输出
            if result.stdout:
                try:
                    ruff_output = json.loads(result.stdout)
                    for item in ruff_output:
                        violations.append(RuleViolation(
                            rule=f"ruff:{item.get('code', 'unknown')}",
                            message=item.get('message', ''),
                            line=item.get('location', {}).get('row', 0),
                            column=item.get('location', {}).get('column', 0),
                            severity=Severity.ERROR if item.get('code', '').startswith('E') else Severity.WARNING,
                            suggestion=item.get('fix', {}).get('message', ''),
                            source="layer1"
                        ))
                except json.JSONDecodeError:
                    pass

        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return violations


class ESLintRule(BaseRule):
    """ESLint JS/TS Linter 封装"""

    name = "eslint"
    layer = 1
    description = "JavaScript/TypeScript 语法和风格检查 (ESLint)"
    supported_languages = ["javascript", "typescript"]

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """
        调用 eslint --format=json 并解析输出

        实现要点:
        1. 检测 eslint 是否可用
        2. 将 content 写入临时文件
        3. 运行 eslint --format=json
        4. 解析输出
        """
        violations = []

        # 检查 eslint 是否可用
        try:
            subprocess.run(["eslint", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # ESLint 未安装，优雅降级（不报错）
            return []

        # 确定文件扩展名
        ext = ".js" if "javascript" in file_path else ".ts"
        temp_file = create_temp_file(content, suffix=ext)

        try:
            # 运行 eslint
            result = subprocess.run(
                ["eslint", "--format=json", temp_file],
                capture_output=True,
                text=True
            )

            # 解析 JSON 输出
            if result.stdout:
                try:
                    eslint_output = json.loads(result.stdout)
                    for file_result in eslint_output:
                        for message in file_result.get('messages', []):
                            severity = Severity.ERROR if message.get('severity') == 2 else Severity.WARNING
                            violations.append(RuleViolation(
                                rule=f"eslint:{message.get('ruleId', 'unknown')}",
                                message=message.get('message', ''),
                                line=message.get('line', 0),
                                column=message.get('column', 0),
                                severity=severity,
                                suggestion=message.get('fix', {}).get('text', ''),
                                source="layer1"
                            ))
                except json.JSONDecodeError:
                    pass

        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return violations
