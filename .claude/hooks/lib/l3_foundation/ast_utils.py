"""
AST 工具模块 - 提供代码解析能力

l3_foundation 基础能力层核心模块
"""

import ast
from typing import List, Optional, Dict, Any


class ASTUtils:
    """AST 解析工具类"""

    @staticmethod
    def parse(content: str) -> Optional[ast.AST]:
        """
        解析代码为 AST

        Args:
            content: 代码内容

        Returns:
            AST 对象，解析失败返回 None
        """
        try:
            return ast.parse(content)
        except SyntaxError:
            return None

    @staticmethod
    def find_functions(tree: ast.AST) -> List[ast.FunctionDef]:
        """
        查找所有函数定义

        Args:
            tree: AST 对象

        Returns:
            函数定义节点列表
        """
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node)
        return functions

    @staticmethod
    def find_classes(tree: ast.AST) -> List[ast.ClassDef]:
        """
        查找所有类定义

        Args:
            tree: AST 对象

        Returns:
            类定义节点列表
        """
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node)
        return classes

    @staticmethod
    def find_decorators(tree: ast.AST) -> List[Dict[str, Any]]:
        """
        查找所有装饰器

        Args:
            tree: AST 对象

        Returns:
            装饰器信息列表
            [
                {"name": "router", "line": 10, "target": "function_name"}
            ]
        """
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

    @staticmethod
    def find_imports(tree: ast.AST) -> List[Dict[str, Any]]:
        """
        查找所有 import 语句

        Args:
            tree: AST 对象

        Returns:
            import 信息列表
            [
                {"type": "import", "module": "os", "line": 1},
                {"type": "from", "module": "typing", "names": ["List"], "line": 2}
            ]
        """
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
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

    @staticmethod
    def find_function_calls(tree: ast.AST, func_name: str) -> List[Dict[str, Any]]:
        """
        查找特定函数的调用

        Args:
            tree: AST 对象
            func_name: 函数名称

        Returns:
            调用信息列表
        """
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    calls.append({
                        "line": node.lineno,
                        "function": func_name
                    })
        return calls

    @staticmethod
    def find_return_statements(tree: ast.AST) -> List[Dict[str, Any]]:
        """
        查找所有 return 语句

        Args:
            tree: AST 对象

        Returns:
            return 信息列表
        """
        returns = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Return):
                returns.append({
                    "line": node.lineno,
                    "has_value": node.value is not None
                })
        return returns

    @staticmethod
    def get_function_source(func: ast.FunctionDef, content: str) -> str:
        """
        提取函数源码

        Args:
            func: 函数定义节点
            content: 完整代码内容

        Returns:
            函数源码
        """
        lines = content.split('\n')
        # 获取函数起始行到结束行
        start_line = func.lineno - 1
        end_line = func.end_lineno if hasattr(func, 'end_lineno') else start_line + 1
        return '\n'.join(lines[start_line:end_line])

    @staticmethod
    def get_function_signature(func: ast.FunctionDef) -> str:
        """
        获取函数签名

        Args:
            func: 函数定义节点

        Returns:
            函数签名字符串
        """
        params = [arg.arg for arg in func.args.args]
        return_type = ast.unparse(func.returns) if func.returns else "None"
        return f"{func.name}({', '.join(params)}) -> {return_type}"

    @staticmethod
    def get_class_methods(cls: ast.ClassDef) -> List[str]:
        """
        获取类的所有方法名

        Args:
            cls: 类定义节点

        Returns:
            方法名列表
        """
        return [node.name for node in cls.body if isinstance(node, ast.FunctionDef)]

    @staticmethod
    def has_decorator(node: ast.AST, decorator_name: str) -> bool:
        """
        检查节点是否有特定装饰器

        Args:
            node: AST 节点
            decorator_name: 装饰器名称

        Returns:
            是否有该装饰器
        """
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            return False

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                return True
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == decorator_name:
                    return True
        return False
