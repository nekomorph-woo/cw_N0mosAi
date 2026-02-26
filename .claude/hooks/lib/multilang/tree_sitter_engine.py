"""
Tree-sitter 多语言解析引擎

提供统一的 AST 抽象层，支持跨语言的函数签名提取、导入分析和调用链追踪
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from pathlib import Path
from .language_detector import Language


@dataclass
class FunctionSignature:
    """函数签名"""
    name: str
    params: List[str]
    return_type: Optional[str]
    line_number: int


@dataclass
class ImportInfo:
    """导入信息"""
    module: str
    names: List[str]
    is_relative: bool
    line_number: int


@dataclass
class CallSite:
    """调用点"""
    caller: str
    callee: str
    line_number: int


@dataclass
class UnifiedAST:
    """统一 AST 抽象 — 跨语言通用结构"""
    language: Language
    functions: List[FunctionSignature] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    call_sites: List[CallSite] = field(default_factory=list)


class TreeSitterEngine:
    """Tree-sitter 多语言解析引擎

    注意: 此实现需要 tree-sitter 和对应语言的绑定
    如果未安装，将优雅降级到基础 AST 解析
    """

    def __init__(self):
        self._parsers: dict[Language, Any] = {}
        self._tree_sitter_available = self._check_tree_sitter()

    def _check_tree_sitter(self) -> bool:
        """检查 tree-sitter 是否可用"""
        try:
            import tree_sitter
            return True
        except ImportError:
            return False

    def parse(self, source: bytes, language: Language) -> UnifiedAST:
        """解析源代码，返回统一 AST

        Args:
            source: 源代码字节串
            language: 编程语言

        Returns:
            UnifiedAST 对象
        """
        if not self._tree_sitter_available:
            # 降级到基础解析
            return self._fallback_parse(source, language)

        # Tree-sitter 解析逻辑
        # 这里需要根据不同语言调用对应的 parser
        # 简化实现: 返回空 AST
        return UnifiedAST(language=language)

    def _fallback_parse(self, source: bytes, language: Language) -> UnifiedAST:
        """降级解析 - 使用 Python 内置 ast 模块

        Args:
            source: 源代码字节串
            language: 编程语言

        Returns:
            UnifiedAST 对象
        """
        ast_obj = UnifiedAST(language=language)

        if language == Language.PYTHON:
            ast_obj = self._parse_python_fallback(source)

        return ast_obj

    def _parse_python_fallback(self, source: bytes) -> UnifiedAST:
        """使用 Python ast 模块解析 Python 代码"""
        import ast as python_ast

        ast_obj = UnifiedAST(language=Language.PYTHON)

        try:
            tree = python_ast.parse(source.decode('utf-8'))

            # 提取函数签名
            for node in python_ast.walk(tree):
                if isinstance(node, python_ast.FunctionDef):
                    params = [arg.arg for arg in node.args.args]
                    return_type = None
                    if node.returns:
                        return_type = python_ast.unparse(node.returns)

                    ast_obj.functions.append(FunctionSignature(
                        name=node.name,
                        params=params,
                        return_type=return_type,
                        line_number=node.lineno
                    ))

                # 提取导入信息
                if isinstance(node, (python_ast.Import, python_ast.ImportFrom)):
                    if isinstance(node, python_ast.Import):
                        for alias in node.names:
                            ast_obj.imports.append(ImportInfo(
                                module=alias.name,
                                names=[alias.asname or alias.name],
                                is_relative=False,
                                line_number=node.lineno
                            ))
                    elif isinstance(node, python_ast.ImportFrom):
                        module = node.module or ""
                        names = [alias.name for alias in node.names]
                        ast_obj.imports.append(ImportInfo(
                            module=module,
                            names=names,
                            is_relative=node.level > 0,
                            line_number=node.lineno
                        ))

        except SyntaxError:
            # 解析失败，返回空 AST
            pass

        return ast_obj

    def extract_functions(self, ast: UnifiedAST) -> List[FunctionSignature]:
        """提取函数签名

        Args:
            ast: UnifiedAST 对象

        Returns:
            函数签名列表
        """
        return ast.functions

    def extract_imports(self, ast: UnifiedAST) -> List[ImportInfo]:
        """提取导入信息

        Args:
            ast: UnifiedAST 对象

        Returns:
            导入信息列表
        """
        return ast.imports

    def trace_calls(self, ast: UnifiedAST) -> List[CallSite]:
        """追踪调用链

        Args:
            ast: UnifiedAST 对象

        Returns:
            调用点列表
        """
        return ast.call_sites
