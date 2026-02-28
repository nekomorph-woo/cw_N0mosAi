"""
第一层规则: 语法和风格检查

Tier 1: Python (Ruff), JS/TS (ESLint) - 原生工具
Tier 2: 其他语言 (Tree-sitter) - 语法检查
"""

import subprocess
import json
import os
import sys
from typing import List
from pathlib import Path
from .base_rule import BaseRule, RuleViolation, Severity
from ..utils import create_temp_file


def _get_venv_bin_path():
    """获取虚拟环境 bin 目录路径"""
    # 方法1: 从当前 Python 可执行文件推断
    python_bin = sys.executable
    if 'site-packages' in python_bin or '.venv' in python_bin or 'venv' in python_bin:
        return os.path.dirname(python_bin)

    # 方法2: 查找项目根目录下的 .venv
    cwd = os.getcwd()
    venv_path = os.path.join(cwd, '.venv', 'bin')
    if os.path.exists(venv_path):
        return venv_path

    # 方法3: 向上查找
    parent = cwd
    for _ in range(5):
        venv_path = os.path.join(parent, '.venv', 'bin')
        if os.path.exists(venv_path):
            return venv_path
        parent = os.path.dirname(parent)
        if parent == '/':
            break

    return None


def _find_executable(name: str) -> str:
    """查找可执行文件路径，优先使用虚拟环境中的"""
    venv_bin = _get_venv_bin_path()
    if venv_bin:
        venv_exe = os.path.join(venv_bin, name)
        if os.path.exists(venv_exe):
            return venv_exe
    return name  # 回退到系统 PATH


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

        # 查找 ruff 可执行文件
        ruff_exe = _find_executable("ruff")

        # 检查 ruff 是否可用
        try:
            subprocess.run([ruff_exe, "--version"], capture_output=True, check=True)
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
                [ruff_exe, "check", "--output-format=json", temp_file],
                capture_output=True,
                text=True
            )

            # 解析 JSON 输出
            if result.stdout:
                try:
                    ruff_output = json.loads(result.stdout)
                    for item in ruff_output:
                        # 安全获取 location (可能为 None)
                        location = item.get('location') or {}
                        fix_info = item.get('fix') or {}

                        # 判断严重程度
                        # - E* (Pycodestyle 错误) → ERROR
                        # - F* (Pyflakes 错误) → ERROR
                        # - syntax 相关 (invalid-syntax 等) → ERROR
                        # - 其他 → WARNING
                        code = item.get('code', '')
                        is_error = (
                            code.startswith('E') or
                            code.startswith('F') or
                            'syntax' in code.lower()
                        )

                        violations.append(RuleViolation(
                            rule=f"ruff:{code}",
                            message=item.get('message', ''),
                            line=location.get('row', 0),
                            column=location.get('column', 0),
                            severity=Severity.ERROR if is_error else Severity.WARNING,
                            suggestion=fix_info.get('message', ''),
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


class TreeSitterRule(BaseRule):
    """Tree-sitter 通用语法检查 (Tier 2)

    用于支持更多编程语言的语法检查
    仅检测语法错误，不提供风格建议
    """

    name = "tree-sitter"
    layer = 1
    description = "多语言语法检查 (Tree-sitter)"
    # 支持的语言由 TreeSitterEngine 动态决定
    supported_languages = [
        "go", "java", "rust", "c", "cpp", "c_sharp",
        "ruby", "php", "swift", "kotlin", "scala",
        "lua", "perl", "r"
    ]

    def __init__(self):
        super().__init__()
        self._engine = None
        self._initialized = False

    def _init_engine(self):
        """延迟初始化 Tree-sitter 引擎"""
        if self._initialized:
            return

        try:
            from ..multilang import TreeSitterEngine, Language
            self._engine = TreeSitterEngine()
        except ImportError:
            self._engine = None

        self._initialized = True

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """使用 Tree-sitter 检查语法错误

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            违规列表
        """
        violations = []

        # 延迟初始化
        self._init_engine()

        if not self._engine:
            # Tree-sitter 不可用，跳过检查
            return violations

        try:
            from ..multilang import Language

            # 检测语言
            detector = self._get_detector()
            language = detector.detect(Path(file_path))

            if language == Language.UNKNOWN:
                return violations

            # 检查语法
            passed, errors = self._engine.check_syntax(content, language)

            for error in errors:
                violations.append(RuleViolation(
                    rule="tree-sitter:syntax-error",
                    message=error.message,
                    line=error.line,
                    column=error.column,
                    severity=Severity.ERROR,
                    suggestion="检查语法是否正确",
                    source="layer1"
                ))

        except Exception:
            # Tree-sitter 检查失败，不阻塞
            pass

        return violations

    def _get_detector(self):
        """获取语言检测器"""
        try:
            from ..multilang import LanguageDetector
            return LanguageDetector()
        except ImportError:
            return None

    def is_applicable(self, language: str) -> bool:
        """判断规则是否适用于指定语言

        Tree-sitter 规则不应用于 Tier 1 语言
        """
        # Tier 1 语言由原生工具处理
        tier1 = {"python", "javascript", "typescript"}
        if language.lower() in tier1:
            return False
        return super().is_applicable(language)
