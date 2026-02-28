"""
动态规则加载模块 - 从 task 目录加载规则脚本

l3_foundation 基础能力层核心模块
带安全沙箱的动态规则加载器
"""

import os
import re
import ast
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional

from .dynamic_rule import DynamicRule, DynamicViolation, Severity


class SecurityError(Exception):
    """安全错误"""
    pass


class DynamicRuleLoader:
    """动态规则加载器 - 从 task 目录加载规则脚本"""

    def __init__(self, strict_mode: bool = True):
        """
        初始化加载器

        Args:
            strict_mode: 严格模式 (True=检测到威胁时拒绝加载)
        """
        self.strict_mode = strict_mode
        self._loaded_rules: Dict[str, List[DynamicRule]] = {}

    def load_from_task(self, task_dir: str) -> List[DynamicRule]:
        """
        从 task 目录加载所有规则

        扫描: {task_dir}/rules/*.py

        Args:
            task_dir: task 目录路径

        Returns:
            规则实例列表
        """
        rules_dir = Path(task_dir) / "rules"
        if not rules_dir.exists():
            return []

        rules = []
        for script_path in rules_dir.glob("*.py"):
            # 跳过 __pycache__ 等
            if script_path.name.startswith("__"):
                continue

            try:
                loaded_rules = self._load_script_securely(script_path)
                if loaded_rules:
                    rules.extend(loaded_rules)
                    # 缓存加载结果
                    self._loaded_rules[str(script_path)] = loaded_rules
            except SecurityError as e:
                print(f"🚨 安全威胁: {script_path.name}: {e}")
                if self.strict_mode:
                    raise
            except SyntaxError as e:
                print(f"⚠️  语法错误: {script_path.name}: {e}")
            except Exception as e:
                print(f"⚠️  加载失败: {script_path.name}: {e}")

        return rules

    def _load_script_securely(self, script_path: Path) -> List[DynamicRule]:
        """
        安全加载单个脚本

        Args:
            script_path: 脚本路径

        Returns:
            规则实例列表

        Raises:
            SecurityError: 检测到安全威胁
            SyntaxError: 语法错误
        """
        # 1. 读取脚本内容
        source = script_path.read_text(encoding='utf-8')

        # 2. 静态安全扫描
        threats = self._static_security_scan(source)
        if threats:
            raise SecurityError(f"静态扫描检测到威胁: {', '.join(threats)}")

        # 3. AST 安全检查
        ast_threats = self._ast_security_check(source)
        if ast_threats:
            raise SecurityError(f"AST 检查检测到威胁: {', '.join(ast_threats)}")

        # 4. 创建沙箱环境
        sandbox_globals = self._create_sandbox_globals()

        # 5. 编译代码
        try:
            code = compile(source, str(script_path), "exec")
        except SyntaxError as e:
            raise SyntaxError(f"语法错误: {e}")

        # 6. 沙箱执行 (带超时)
        try:
            self._exec_with_timeout(code, sandbox_globals, timeout=5)
        except TimeoutError:
            raise SecurityError("脚本执行超时 (可能包含无限循环)")

        # 7. 提取所有 DynamicRule 子类和函数式规则
        rules = []
        for name, obj in sandbox_globals.items():
            # 方式 1: 类继承风格 (继承 DynamicRule)
            if (isinstance(obj, type) and
                issubclass(obj, DynamicRule) and
                obj is not DynamicRule):
                try:
                    # 实例化规则
                    rule_instance = obj()
                    rules.append(rule_instance)
                except Exception as e:
                    print(f"⚠️  规则实例化失败: {name}: {e}")

            # 方式 2: 函数式风格 (有 check 和 should_check 函数)
            # 函数式规则通过元数据标识: name, layer, handler_type
            if name == "check" and callable(obj):
                # 检查是否有函数式规则的标识
                rule_meta = sandbox_globals.get("name")
                if rule_meta and isinstance(rule_meta, str):
                    try:
                        # 创建函数式规则的包装类
                        class FunctionalRuleWrapper(DynamicRule):
                            name = sandbox_globals.get("name", "unknown")
                            layer = sandbox_globals.get("layer", 3)
                            description = sandbox_globals.get("description", "")
                            handler_type = sandbox_globals.get("handler_type", "command")

                            def __init__(self):
                                super().__init__(config=sandbox_globals.get("config", {}))
                                self._check_fn = obj
                                self._should_check_fn = sandbox_globals.get("should_check")

                            def check(self, file_path: str, content: str) -> List[DynamicViolation]:
                                return self._check_fn(file_path, content) if self._check_fn else []

                            def should_check(self, file_path: str) -> bool:
                                if self._should_check_fn and callable(self._should_check_fn):
                                    return self._should_check_fn(file_path)
                                return True

                        rule_instance = FunctionalRuleWrapper()
                        rules.append(rule_instance)
                        break  # 只处理一次函数式规则
                    except Exception as e:
                        print(f"⚠️  函数式规则包装失败: {e}")

        return rules

    def _static_security_scan(self, source: str) -> List[str]:
        """
        静态安全扫描 - 正则匹配危险模式

        Args:
            source: 脚本源码

        Returns:
            检测到的威胁列表
        """
        threats = []

        # 危险模式列表 (使用原始字符串避免转义问题)
        dangerous_patterns = [
            (r"import\s+os\b", "禁止导入 os 模块"),
            (r"import\s+subprocess", "禁止导入 subprocess 模块"),
            (r"import\s+sys\b", "禁止导入 sys 模块"),
            (r"from\s+os\s+import", "禁止从 os 导入"),
            (r"from\s+subprocess\s+import", "禁止从 subprocess 导入"),
            (r"from\s+sys\s+import", "禁止从 sys 导入"),
            (r"__import__\s*\(", "禁止使用 __import__"),
            (r"\beval\s*\(", "禁止使用 eval()"),
            (r"\bexec\s*\(", "禁止使用 exec()"),
            (r"\bopen\s*\(", "禁止使用 open()"),
            (r"\bcompile\s*\(", "禁止使用 compile()"),
            (r"__builtins__", "禁止访问 __builtins__"),
            (r"\bglobals\s*\(", "禁止使用 globals()"),
            (r"\blocals\s*\(", "禁止使用 locals()"),
        ]

        for pattern, message in dangerous_patterns:
            if re.search(pattern, source):
                threats.append(message)

        return threats

    def _ast_security_check(self, source: str) -> List[str]:
        """
        AST 安全检查

        Args:
            source: 脚本源码

        Returns:
            检测到的威胁列表
        """
        threats = []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ["语法错误"]

        # 危险模块列表
        dangerous_modules = {"os", "subprocess", "sys", "socket", "urllib", "http", "ftplib"}

        # 危险函数列表
        dangerous_functions = {
            "eval", "exec", "compile", "open", "__import__",
            "globals", "locals", "vars", "dir"
        }

        for node in ast.walk(tree):
            # 检查 import 语句
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in dangerous_modules:
                        threats.append(f"禁止导入模块: {alias.name}")

            # 检查 from ... import 语句
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in dangerous_modules:
                    threats.append(f"禁止从模块导入: {node.module}")

            # 检查函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous_functions:
                        threats.append(f"禁止调用函数: {node.func.id}")

            # 检查属性访问
            if isinstance(node, ast.Attribute):
                if node.attr in {"__builtins__", "__globals__", "__code__"}:
                    threats.append(f"禁止访问属性: {node.attr}")

        return threats

    def _create_sandbox_globals(self) -> Dict[str, Any]:
        """
        创建沙箱执行环境

        Returns:
            受限的 globals 命名空间
        """
        # 1. 创建受限的 builtins
        safe_builtins = {
            # Python 3 类创建必需
            "__build_class__": __builtins__["__build_class__"],

            # 允许的内置函数
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "isinstance": isinstance,
            "issubclass": issubclass,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "range": range,
            "reversed": reversed,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "type": type,
            "zip": zip,

            # 允许的异常
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "NotImplementedError": NotImplementedError,

            # 禁止的函数 (设为 None)
            "eval": None,
            "exec": None,
            "compile": None,
            "open": None,
            "__import__": None,
            "globals": None,
            "locals": None,
        }

        # 导入 l3_foundation 模块
        from . import dynamic_rule, ai_client, ast_utils, prompt_builder, rule_context

        # 2. 注入白名单模块
        sandbox_globals = {
            "__builtins__": safe_builtins,
            "__name__": "__rules__",
            "__file__": "dynamic_rule.py",

            # 注入 l3_foundation 基础能力
            "DynamicRule": dynamic_rule.DynamicRule,
            "DynamicViolation": dynamic_rule.DynamicViolation,
            "Severity": dynamic_rule.Severity,
            "FileMatcher": dynamic_rule.FileMatcher,
            "AIClient": ai_client.AIClient,
            "ASTUtils": ast_utils.ASTUtils,
            "PromptBuilder": prompt_builder.PromptBuilder,
            "RuleContext": rule_context.RuleContext,

            # 允许的标准库模块 (受限)
            "re": re,
            "ast": ast,
        }

        return sandbox_globals

    def _exec_with_timeout(self, code, globals_dict: Dict, timeout: int = 5):
        """
        带超时的执行

        Args:
            code: 编译后的代码对象
            globals_dict: 全局命名空间
            timeout: 超时秒数

        Raises:
            TimeoutError: 执行超时
        """
        def timeout_handler(signum, frame):
            raise TimeoutError("脚本执行超时")

        # 设置旧的超时处理
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)

        try:
            signal.alarm(timeout)
            exec(code, globals_dict)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


def load_rules_from_task(task_dir: str, strict_mode: bool = True) -> List[DynamicRule]:
    """
    便捷函数: 从 task 目录加载规则

    Args:
        task_dir: task 目录路径
        strict_mode: 严格模式

    Returns:
        动态规则实例列表
    """
    loader = DynamicRuleLoader(strict_mode=strict_mode)
    return loader.load_from_task(task_dir)
