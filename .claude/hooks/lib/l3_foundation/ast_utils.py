"""
AST 工具模块 - 提供多语言代码解析能力

l3_foundation 基础能力层核心模块
使用 multilang 模块实现跨语言支持
"""

from typing import List, Optional, Dict, Any
from pathlib import Path


class ASTUtils:
    """AST 解析工具类 (多语言版本)"""

    def __init__(self):
        """初始化 AST 工具，延迟加载 multilang 依赖"""
        self._language_detector = None
        self._tree_sitter_engine = None
        self._Language = None
        self._UnifiedAST = None

    def _ensure_multilang(self):
        """延迟加载 multilang 模块"""
        if self._language_detector is None:
            try:
                from ..multilang import LanguageDetector, Language
                from ..multilang import TreeSitterEngine, UnifiedAST

                self._language_detector = LanguageDetector()
                self._tree_sitter_engine = TreeSitterEngine()
                self._Language = Language
                self._UnifiedAST = UnifiedAST
            except ImportError:
                # multilang 不可用，使用 Python 原生 ast 作为降级
                import ast
                from enum import Enum

                class Language(Enum):
                    PYTHON = "python"
                    UNKNOWN = "unknown"

                self._language_detector = _SimpleLanguageDetector()
                self._Language = Language
                self._tree_sitter_engine = _PythonASTEngine()
                self._UnifiedAST = dict  # 降级使用 dict

    @staticmethod
    def parse(content: str, file_path: str = None) -> Optional[Any]:
        """
        解析代码为 AST (多语言)

        Args:
            content: 代码内容
            file_path: 文件路径 (用于语言检测)

        Returns:
            AST 对象，解析失败返回 None
        """
        utils = ASTUtils()
        utils._ensure_multilang()

        # 检测语言
        language = utils._Language.UNKNOWN
        if file_path:
            language = utils._language_detector.detect(Path(file_path))

        # 解析
        return utils._tree_sitter_engine.parse(
            content.encode('utf-8'),
            language
        )

    @staticmethod
    def find_functions(tree: Any) -> List[Any]:
        """
        查找所有函数定义 (多语言)

        Args:
            tree: AST 对象

        Returns:
            函数定义节点列表
        """
        # 如果是 UnifiedAST
        if hasattr(tree, 'functions'):
            return tree.functions

        # 如果是 Python ast tree
        try:
            import ast
            if isinstance(tree, ast.AST):
                functions = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        functions.append(node)
                return functions
        except ImportError:
            pass

        return []

    @staticmethod
    def find_classes(tree: Any) -> List[Any]:
        """
        查找所有类定义 (多语言)

        Args:
            tree: AST 对象

        Returns:
            类定义节点列表
        """
        # 如果是 Python ast tree
        try:
            import ast
            if isinstance(tree, ast.AST):
                classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes.append(node)
                return classes
        except ImportError:
            pass

        return []

    @staticmethod
    def find_imports(tree: Any) -> List[Dict[str, Any]]:
        """
        查找所有 import 语句 (多语言)

        Args:
            tree: AST 对象

        Returns:
            import 信息列表
        """
        # 如果是 UnifiedAST
        if hasattr(tree, 'imports'):
            return [
                {
                    "type": "from" if imp.is_relative else "import",
                    "module": imp.module,
                    "names": imp.names,
                    "line": imp.line_number
                }
                for imp in tree.imports
            ]

        # 如果是 Python ast tree
        try:
            import ast
            if isinstance(tree, ast.AST):
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append({
                                "type": "import",
                                "module": alias.name,
                                "names": [alias.asname or alias.name],
                                "line": node.lineno
                            })
                    elif isinstance(node, ast.ImportFrom):
                        imports.append({
                            "type": "from",
                            "module": node.module or "",
                            "names": [alias.name for alias in node.names],
                            "line": node.lineno
                        })
                return imports
        except ImportError:
            pass

        return []

    @staticmethod
    def find_function_calls(tree: Any, func_name: str) -> List[Dict[str, Any]]:
        """
        查找特定函数的调用 (多语言)

        Args:
            tree: AST 对象
            func_name: 函数名称

        Returns:
            调用信息列表
        """
        # 如果是 UnifiedAST，使用 call_sites
        if hasattr(tree, 'call_sites'):
            return [
                {
                    "line": call.line_number,
                    "function": func_name,
                    "caller": call.caller
                }
                for call in tree.call_sites
                if call.callee == func_name
            ]

        # 降级：简单字符串匹配
        return []

    @staticmethod
    def find_decorators(tree: Any) -> List[Dict[str, Any]]:
        """
        查找所有装饰器 (多语言)

        Args:
            tree: AST 对象

        Returns:
            装饰器信息列表
        """
        # Python 特有
        try:
            import ast
            if isinstance(tree, ast.AST):
                decorators = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name):
                                decorators.append({
                                    "name": decorator.id,
                                    "line": decorator.lineno,
                                    "target": node.name
                                })
                            elif isinstance(decorator, ast.Call):
                                if isinstance(decorator.func, ast.Name):
                                    decorators.append({
                                        "name": decorator.func.id,
                                        "line": decorator.lineno,
                                        "target": node.name,
                                        "has_args": True
                                    })
                return decorators
        except ImportError:
            pass

        return []

    @staticmethod
    def get_function_source(func: Any, content: str) -> str:
        """
        提取函数源码

        Args:
            func: 函数定义节点
            content: 完整代码内容

        Returns:
            函数源码
        """
        lines = content.split('\n')
        start_line = func.lineno - 1
        end_line = func.end_lineno if hasattr(func, 'end_lineno') else start_line + 1
        return '\n'.join(lines[start_line:end_line])

    @staticmethod
    def get_function_signature(func: Any) -> str:
        """
        获取函数签名

        Args:
            func: 函数定义节点

        Returns:
            函数签名字符串
        """
        # 如果是 FunctionSignature dataclass
        if hasattr(func, 'name') and hasattr(func, 'params'):
            return_type = func.return_type or 'None'
            return f"{func.name}({', '.join(func.params)}) -> {return_type}"

        # 如果是 Python ast FunctionDef
        try:
            import ast
            if isinstance(func, ast.FunctionDef):
                params = [arg.arg for arg in func.args.args]
                return_type = ast.unparse(func.returns) if func.returns else "None"
                return f"{func.name}({', '.join(params)}) -> {return_type}"
        except ImportError:
            pass

        return str(func)

    @staticmethod
    def get_class_methods(cls: Any) -> List[str]:
        """
        获取类的所有方法名

        Args:
            cls: 类定义节点

        Returns:
            方法名列表
        """
        try:
            import ast
            if isinstance(cls, ast.ClassDef):
                return [node.name for node in cls.body if isinstance(node, ast.FunctionDef)]
        except ImportError:
            pass

        return []

    @staticmethod
    def has_decorator(node: Any, decorator_name: str) -> bool:
        """
        检查节点是否有特定装饰器

        Args:
            node: AST 节点
            decorator_name: 装饰器名称

        Returns:
            是否有该装饰器
        """
        try:
            import ast
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                        return True
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == decorator_name:
                            return True
        except ImportError:
            pass

        return False


# 降级实现：简单的语言检测器
class _SimpleLanguageDetector:
    """简单的语言检测器 (降级实现)"""

    def detect(self, path: Path):
        """根据文件扩展名检测语言"""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".java": "java",
        }
        lang = ext_map.get(path.suffix, "unknown")

        class Enum:
            PYTHON = "python"
            JAVASCRIPT = "javascript"
            TYPESCRIPT = "typescript"
            GO = "go"
            JAVA = "java"
            UNKNOWN = "unknown"

        return getattr(Enum, lang.upper(), Enum.UNKNOWN)


# 降级实现：Python AST 引擎
class _PythonASTEngine:
    """Python AST 引擎 (降级实现)"""

    class UnifiedAST:
        def __init__(self, language):
            self.language = language
            self.functions = []
            self.imports = []
            self.call_sites = []

    def parse(self, source, language):
        """使用 Python ast 模块解析"""
        import ast

        ast_obj = self.UnifiedAST(language)

        try:
            tree = ast.parse(source.decode('utf-8'))

            # 提取函数
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    params = [arg.arg for arg in node.args.args]
                    return_type = ast.unparse(node.returns) if node.returns else None
                    ast_obj.functions.append(type('Node', (), {
                        'name': node.name,
                        'params': params,
                        'return_type': return_type,
                        'lineno': node.lineno,
                        'end_lineno': node.end_lineno
                    })())

                # 提取导入
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        ast_obj.imports.append(type('Node', (), {
                            'module': alias.name,
                            'names': [alias.asname or alias.name],
                            'is_relative': False,
                            'line_number': node.lineno
                        })())
                elif isinstance(node, ast.ImportFrom):
                    names = [alias.name for alias in node.names]
                    ast_obj.imports.append(type('Node', (), {
                        'module': node.module or "",
                        'names': names,
                        'is_relative': node.level > 0,
                        'line_number': node.lineno
                    })())

        except SyntaxError:
            pass

        return ast_obj
