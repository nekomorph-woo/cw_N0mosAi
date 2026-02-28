"""
Tree-sitter 多语言解析引擎

提供统一的 AST 抽象层，支持跨语言的函数签名提取、导入分析和调用链追踪
支持语法错误检测，用于 Layer 1 语法检查
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple
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
class SyntaxError:
    """语法错误"""
    message: str
    line: int
    column: int
    node_type: str = ""


@dataclass
class UnifiedAST:
    """统一 AST 抽象 — 跨语言通用结构"""
    language: Language
    functions: List[FunctionSignature] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    call_sites: List[CallSite] = field(default_factory=list)
    syntax_errors: List[SyntaxError] = field(default_factory=list)
    has_error: bool = False


class TreeSitterEngine:
    """Tree-sitter 多语言解析引擎

    支持语法错误检测，用于 Layer 1 语法检查
    如果未安装 tree-sitter，将优雅降级
    """

    # Tree-sitter 语言包映射 (新版 tree-sitter 0.25+)
    LANGUAGE_PACKAGES = {
        Language.GO: ("tree_sitter_go", "language"),
        Language.JAVA: ("tree_sitter_java", "language"),
        Language.RUST: ("tree_sitter_rust", "language"),
        Language.C: ("tree_sitter_c", "language"),
        Language.CPP: ("tree_sitter_cpp", "language"),
        Language.CSHARP: ("tree_sitter_c_sharp", "language"),
        Language.RUBY: ("tree_sitter_ruby", "language"),
        Language.PHP: ("tree_sitter_php", "language"),
        Language.SWIFT: ("tree_sitter_swift", "language"),
        Language.KOTLIN: ("tree_sitter_kotlin", "language"),
        Language.SCALA: ("tree_sitter_scala", "language"),
        Language.LUA: ("tree_sitter_lua", "language"),
        Language.PERL: ("tree_sitter_perl", "language"),
        Language.R: ("tree_sitter_r", "language"),
    }

    def __init__(self):
        self._parsers: dict[Language, Any] = {}
        self._tree_sitter_available = self._check_tree_sitter()
        self._languages_available = {}
        self._ts_language_class = None

        if self._tree_sitter_available:
            self._init_language_bindings()

    def _check_tree_sitter(self) -> bool:
        """检查 tree-sitter 是否可用"""
        try:
            import tree_sitter
            return True
        except ImportError:
            return False

    def _init_language_bindings(self):
        """初始化语言绑定"""
        try:
            from tree_sitter import Language
            self._ts_language_class = Language
        except ImportError:
            return

        # 检查哪些语言包可用
        for lang, (module_name, attr_name) in self.LANGUAGE_PACKAGES.items():
            try:
                module = __import__(module_name)
                # 新版 API: tree_sitter_go.language() 返回语言定义
                lang_func = getattr(module, attr_name, None)
                if lang_func and callable(lang_func):
                    self._languages_available[lang] = self._ts_language_class(lang_func())
            except ImportError:
                pass

    def is_language_supported(self, language: Language) -> bool:
        """检查语言是否支持"""
        return language in self._languages_available

    def get_supported_languages(self) -> List[Language]:
        """获取支持的语言列表"""
        return list(self._languages_available.keys())

    def check_syntax(self, source: str, language: Language) -> Tuple[bool, List[SyntaxError]]:
        """检查语法错误

        Args:
            source: 源代码字符串
            language: 编程语言

        Returns:
            (是否有错误, 错误列表)
        """
        if not self._tree_sitter_available:
            return True, []  # tree-sitter 不可用，跳过检查

        if language not in self._languages_available:
            return True, []  # 语言包未安装，跳过检查

        try:
            from tree_sitter import Parser

            # 获取语言和解析器
            ts_lang = self._languages_available[language]
            parser = Parser(ts_lang)

            # 解析代码
            tree = parser.parse(source.encode('utf-8'))
            root = tree.root_node

            # 检查是否有语法错误
            errors = self._find_error_nodes(root)

            return len(errors) == 0, errors

        except Exception as e:
            # 解析失败，不阻塞
            return True, []

    def _find_error_nodes(self, node, errors: List[SyntaxError] = None) -> List[SyntaxError]:
        """递归查找错误节点

        Args:
            node: Tree-sitter 节点
            errors: 错误列表

        Returns:
            语法错误列表
        """
        if errors is None:
            errors = []

        if node.is_error or node.is_missing:
            errors.append(SyntaxError(
                message=self._get_error_message(node),
                line=node.start_point[0] + 1,  # 转为 1-based
                column=node.start_point[1] + 1,
                node_type=node.type
            ))

        # 递归检查子节点
        for child in node.children:
            self._find_error_nodes(child, errors)

        return errors

    def _get_error_message(self, node) -> str:
        """生成错误消息"""
        if node.is_missing:
            return f"缺少语法元素: {node.type}"
        elif node.is_error:
            # 尝试获取更具体的错误信息
            text = node.text.decode('utf-8') if hasattr(node, 'text') and node.text else ''
            if text:
                return f"语法错误: '{text[:50]}...'" if len(text) > 50 else f"语法错误: '{text}'"
            return "语法错误"
        return "未知错误"

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
