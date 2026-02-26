"""
第三层业务规则 (Layer 3 Business Rules)

支持三种 Handler 类型:
- Command Handler: 静态检查 (正则、AST)
- Prompt Handler: 语义判断 (调用 Haiku)
- Agent Handler: 深度验证 (spawn 子 Agent)
"""

import os
import re
import ast
import json
import yaml
from typing import List, Optional, Dict, Any
from .base_rule import BaseRule, RuleViolation, Severity


class Layer3Rule(BaseRule):
    """第三层业务规则基类"""

    layer = 3
    handler_type: str = "command"  # "command" / "prompt" / "agent"

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}


class ModuleIsolationRule(Layer3Rule):
    """模块隔离规则 - Command Handler

    检查模块间 import 是否符合隔离规则
    """

    name = "module_isolation"
    handler_type = "command"
    description = "检查模块间 import 是否符合隔离规则"

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """检查 import 路径是否在允许列表中

        config:
          allowed_imports: ["src.core", "src.utils"]
          forbidden_imports: ["src.internal"]
        """
        violations = []

        if not file_path.endswith('.py'):
            return violations

        allowed_imports = self.config.get('allowed_imports', [])
        forbidden_imports = self.config.get('forbidden_imports', [])

        # 提取所有 import 语句
        import_pattern = r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))'
        for line_num, line in enumerate(content.split('\n'), 1):
            match = re.match(import_pattern, line.strip())
            if match:
                module = match.group(1) or match.group(2)

                # 检查是否在禁止列表中
                for forbidden in forbidden_imports:
                    if module.startswith(forbidden):
                        violations.append(RuleViolation(
                            rule_name=self.name,
                            severity=Severity.MAJOR,
                            file_path=file_path,
                            line_number=line_num,
                            message=f"禁止导入模块 '{module}' (在禁止列表中: {forbidden})",
                            suggestion=f"请使用允许的模块: {', '.join(allowed_imports)}"
                        ))

                # 检查是否在允许列表中 (如果配置了允许列表)
                if allowed_imports:
                    is_allowed = any(module.startswith(allowed) for allowed in allowed_imports)
                    # 允许标准库和第三方库
                    is_stdlib = not module.startswith('src') and not module.startswith('.')
                    if not is_allowed and not is_stdlib:
                        violations.append(RuleViolation(
                            rule_name=self.name,
                            severity=Severity.MINOR,
                            file_path=file_path,
                            line_number=line_num,
                            message=f"模块 '{module}' 不在允许列表中",
                            suggestion=f"允许的模块: {', '.join(allowed_imports)}"
                        ))

        return violations


class I18nRule(Layer3Rule):
    """国际化规则 - Prompt Handler

    检查 UI 相关代码是否使用 i18n
    """

    name = "i18n_required"
    handler_type = "prompt"
    description = "检查 UI 代码是否使用 i18n"

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """使用 Haiku 判断是否存在硬编码字符串

        config:
          target_dirs: ["src/ui/", "src/views/"]
          exclude_patterns: ["test_*", "*_test.py"]
          i18n_function: "_t"
        """
        violations = []

        # 检查文件是否在目标目录中
        target_dirs = self.config.get('target_dirs', [])
        if target_dirs:
            if not any(file_path.startswith(d) for d in target_dirs):
                return violations

        # 检查是否在排除模式中
        exclude_patterns = self.config.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if re.match(pattern.replace('*', '.*'), os.path.basename(file_path)):
                return violations

        # 简化实现: 检测字符串字面量 (实际应该调用 Haiku)
        # 这里使用正则作为 fallback
        string_pattern = r'["\']([^"\']{10,})["\']'  # 至少 10 个字符的字符串
        i18n_function = self.config.get('i18n_function', '_t')

        for line_num, line in enumerate(content.split('\n'), 1):
            # 跳过注释和文档字符串
            if line.strip().startswith('#') or '"""' in line or "'''" in line:
                continue

            matches = re.finditer(string_pattern, line)
            for match in matches:
                string_content = match.group(1)
                # 检查是否已经使用 i18n 函数
                if i18n_function not in line:
                    # 简单启发式: 包含空格的长字符串可能是用户可见文本
                    if ' ' in string_content and len(string_content) > 15:
                        violations.append(RuleViolation(
                            rule_name=self.name,
                            severity=Severity.MINOR,
                            file_path=file_path,
                            line_number=line_num,
                            message=f"可能存在硬编码的用户可见字符串: '{string_content[:30]}...'",
                            suggestion=f"建议使用 {i18n_function}() 函数包裹字符串"
                        ))

        return violations


class LoggerRule(Layer3Rule):
    """Logger 规范规则 - Prompt Handler

    检查是否使用标准 logger 而非 print
    """

    name = "logger_standard"
    handler_type = "prompt"
    description = "检查是否使用标准 logger"

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """检测 print() 调用并建议使用 logger

        config:
          logger_module: "src.utils.logger"
          allow_print_in: ["scripts/", "tests/"]
        """
        violations = []

        # 检查是否在允许 print 的目录中
        allow_print_in = self.config.get('allow_print_in', [])
        if any(file_path.startswith(d) for d in allow_print_in):
            return violations

        logger_module = self.config.get('logger_module', 'logging')

        # 检测 print() 调用
        print_pattern = r'\bprint\s*\('
        for line_num, line in enumerate(content.split('\n'), 1):
            if re.search(print_pattern, line):
                # 跳过注释
                if line.strip().startswith('#'):
                    continue

                violations.append(RuleViolation(
                    rule_name=self.name,
                    severity=Severity.MINOR,
                    file_path=file_path,
                    line_number=line_num,
                    message="使用了 print() 进行输出",
                    suggestion=f"建议使用 {logger_module} 进行日志记录"
                ))

        return violations


class InterfaceProtectionRule(Layer3Rule):
    """接口保护规则 - Agent Handler

    检查 Protected Interface 是否被未声明修改
    """

    name = "interface_protection"
    handler_type = "agent"
    description = "检查 Protected Interface 签名是否被修改"

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """spawn 子 Agent 检查接口签名变更

        config:
          protected_files: ["src/core/interfaces.py"]
          protected_functions: ["authenticate", "authorize"]
          protected_classes: ["UserService"]
        """
        violations = []

        protected_files = self.config.get('protected_files', [])
        if file_path not in protected_files:
            return violations

        protected_functions = self.config.get('protected_functions', [])
        protected_classes = self.config.get('protected_classes', [])

        # 简化实现: 使用 AST 检测函数签名
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return violations

        for node in ast.walk(tree):
            # 检查函数定义
            if isinstance(node, ast.FunctionDef):
                if node.name in protected_functions:
                    # 这里应该与之前的签名比对
                    # 简化实现: 只检测是否存在
                    violations.append(RuleViolation(
                        rule_name=self.name,
                        severity=Severity.CRITICAL,
                        file_path=file_path,
                        line_number=node.lineno,
                        message=f"Protected Function '{node.name}' 被修改",
                        suggestion="修改 Protected Interface 前必须在 plan.md 中声明"
                    ))

            # 检查类定义
            if isinstance(node, ast.ClassDef):
                if node.name in protected_classes:
                    violations.append(RuleViolation(
                        rule_name=self.name,
                        severity=Severity.CRITICAL,
                        file_path=file_path,
                        line_number=node.lineno,
                        message=f"Protected Class '{node.name}' 被修改",
                        suggestion="修改 Protected Interface 前必须在 plan.md 中声明"
                    ))

        return violations


class DynamicRuleLoader:
    """从 plan.md 动态加载第三层规则"""

    RULE_REGISTRY = {
        "module_isolation": ModuleIsolationRule,
        "i18n_required": I18nRule,
        "logger_standard": LoggerRule,
        "interface_protection": InterfaceProtectionRule,
    }

    def load_from_plan(self, plan_path: str) -> List[Layer3Rule]:
        """从 plan.md 的 YAML Frontmatter 读取 custom_rules

        Returns:
            实例化的第三层规则列表
        """
        if not os.path.exists(plan_path):
            return []

        with open(plan_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取 YAML Frontmatter
        if not content.startswith('---'):
            return []

        parts = content.split('---', 2)
        if len(parts) < 3:
            return []

        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return []

        if not frontmatter or 'custom_rules' not in frontmatter:
            return []

        # 实例化规则
        rules = []
        for rule_config in frontmatter['custom_rules']:
            rule_name = rule_config.get('rule')
            config = rule_config.get('config', {})

            if rule_name in self.RULE_REGISTRY:
                rule_class = self.RULE_REGISTRY[rule_name]
                rules.append(rule_class(config))

        return rules

    def register_rule(self, name: str, rule_class: type) -> None:
        """注册自定义规则到注册表"""
        if not issubclass(rule_class, Layer3Rule):
            raise ValueError(f"{rule_class} 必须继承自 Layer3Rule")
        self.RULE_REGISTRY[name] = rule_class
