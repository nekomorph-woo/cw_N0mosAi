"""
第三层业务规则 - 预制规则集 (Layer 3 Preset Rules)

这些是通用的预制规则，适用于大多数项目。
项目特定的动态规则请使用 l3_foundation.rule_generator 从 plan.md 生成。

预制规则:
- ModuleIsolationRule: 模块隔离检查
- I18nRule: 国际化检查
- LoggerRule: Logger 规范检查
- InterfaceProtectionRule: 接口保护检查
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

# 从 l3_foundation 导入基础类
from ..l3_foundation import BaseRule, RuleViolation, Severity
from ..l3_foundation import AIClient, ASTUtils


# =============================================================================
# 预制规则 1: 模块隔离规则
# =============================================================================

class ModuleIsolationRule(BaseRule):
    """模块隔离规则 - Command Handler

    检查模块间 import 是否符合隔离规则

    配置:
      - allowed_imports: ["src.core", "src.utils"]
      - forbidden_imports: ["src.internal"]
    """

    name = "module_isolation"
    layer = 3
    handler_type = "command"
    description = "检查模块间 import 是否符合隔离规则"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
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
                            rule=self.name,
                            message=f"禁止导入模块 '{module}' (在禁止列表中: {forbidden})",
                            line=line_num,
                            column=0,
                            severity=Severity.ERROR,
                            suggestion=f"请使用允许的模块: {', '.join(allowed_imports)}"
                        ))

                # 检查是否在允许列表中 (如果配置了允许列表)
                if allowed_imports:
                    is_allowed = any(module.startswith(allowed) for allowed in allowed_imports)
                    # 允许标准库和第三方库
                    is_stdlib = not module.startswith('src') and not module.startswith('.')
                    if not is_allowed and not is_stdlib:
                        violations.append(RuleViolation(
                            rule=self.name,
                            message=f"模块 '{module}' 不在允许列表中",
                            line=line_num,
                            column=0,
                            severity=Severity.WARNING,
                            suggestion=f"允许的模块: {', '.join(allowed_imports)}"
                        ))

        return violations

    def should_check(self, file_path: str) -> bool:
        return file_path.endswith('.py')


# =============================================================================
# 预制规则 2: 国际化规则
# =============================================================================

class I18nRule(BaseRule):
    """国际化规则 - Prompt Handler

    检查 UI 相关代码是否使用 i18n

    配置:
      - target_dirs: ["src/ui", "src/components"]
      - exclude_patterns: ["*.test.py"]
      - i18n_function: "_t" (默认)
    """

    name = "i18n_required"
    layer = 3
    handler_type = "prompt"
    description = "检查 UI 代码是否使用 i18n"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.ai_client = AIClient()

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        violations = []

        # 快速预检
        if not self._should_check(file_path, content):
            return violations

        # AI 判断 (如果可用)
        if self.ai_client.available:
            prompt = self._build_prompt()
            result = self.ai_client.call(prompt, content)
            if result:
                return self._parse_ai_result(result)

        # 降级到正则检查
        return self._fallback_check(file_path, content)

    def _should_check(self, file_path: str, content: str) -> bool:
        """快速预检"""
        # 检查文件是否在目标目录中
        target_dirs = self.config.get('target_dirs', [])
        if target_dirs and not any(file_path.startswith(d) for d in target_dirs):
            return False

        # 检查是否在排除模式中
        exclude_patterns = self.config.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if re.match(pattern.replace('*', '.*'), os.path.basename(file_path)):
                return False

        # 没有长字符串字面量, 直接通过
        if not re.search(r'["\'][^"\']{10,}["\']', content):
            return False

        return True

    def _build_prompt(self) -> str:
        """构建 AI prompt"""
        i18n_func = self.config.get('i18n_function', '_t')
        return f"""你是代码审查专家。检查代码中的硬编码字符串。

规则:
1. 用户可见的 UI 文本必须使用 {i18n_func}() 函数包装
2. 日志/调试信息可以硬编码
3. 错误消息应该使用 i18n
4. 注释中的字符串不需要处理

返回 JSON 格式:
{{
  "violations": [
    {{"line": 10, "text": "Hello World", "reason": "UI文本未国际化"}}
  ]
}}

如果没有违规, 返回: {{"violations": []}}"""

    def _parse_ai_result(self, result: Dict) -> List[RuleViolation]:
        """解析 AI 返回结果"""
        violations = []
        i18n_func = self.config.get('i18n_function', '_t')

        for item in result.get('violations', []):
            line_num = item.get('line', 0)
            text = item.get('text', '')
            reason = item.get('reason', '硬编码字符串')

            violations.append(RuleViolation(
                rule=self.name,
                message=f"{reason}: '{text[:30]}{'...' if len(text) > 30 else ''}'",
                line=line_num,
                column=0,
                severity=Severity.WARNING,
                suggestion=f"使用 {i18n_func}() 包装字符串"
            ))

        return violations

    def _fallback_check(self, file_path: str, content: str) -> List[RuleViolation]:
        """正则降级检查"""
        violations = []
        i18n_func = self.config.get('i18n_function', '_t')
        string_pattern = r'["\']([^"\']{10,})["\']'

        for line_num, line in enumerate(content.split('\n'), 1):
            # 跳过注释和文档字符串
            if line.strip().startswith('#') or '"""' in line or "'''" in line:
                continue

            matches = re.finditer(string_pattern, line)
            for match in matches:
                string_content = match.group(1)
                # 检查是否已经使用 i18n 函数
                if i18n_func not in line:
                    # 简单启发式: 包含空格的长字符串可能是用户可见文本
                    if ' ' in string_content and len(string_content) > 15:
                        violations.append(RuleViolation(
                            rule=self.name,
                            message=f"可能存在硬编码的用户可见字符串: '{string_content[:30]}...'",
                            line=line_num,
                            column=0,
                            severity=Severity.WARNING,
                            suggestion=f"建议使用 {i18n_func}() 函数包裹字符串"
                        ))

        return violations


# =============================================================================
# 预制规则 3: Logger 规范规则
# =============================================================================

class LoggerRule(BaseRule):
    """Logger 规范规则 - Prompt Handler

    检查是否使用标准 logger 而非 print

    配置:
      - allow_print_in: ["tests", "scripts"]
      - logger_module: "logging" (默认)
    """

    name = "logger_standard"
    layer = 3
    handler_type = "prompt"
    description = "检查是否使用标准 logger"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.ai_client = AIClient()

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        violations = []

        # 快速预检
        if not self._should_check(file_path, content):
            return violations

        # AI 判断 (如果可用)
        if self.ai_client.available:
            prompt = self._build_prompt()
            result = self.ai_client.call(prompt, content)
            if result:
                return self._parse_ai_result(result)

        # 降级到正则检查
        return self._fallback_check(file_path, content)

    def _should_check(self, file_path: str, content: str) -> bool:
        """快速预检"""
        # 检查是否在允许 print 的目录中
        allow_print_in = self.config.get('allow_print_in', [])
        if any(file_path.startswith(d) for d in allow_print_in):
            return False

        # 没有 print() 调用, 直接通过
        if not re.search(r'\bprint\s*\(', content):
            return False

        return True

    def _build_prompt(self) -> str:
        """构建 AI prompt"""
        return """你是代码审查专家。检查代码中的 print() 使用情况。

规则:
1. 业务代码中不应使用 print(), 应使用 logger
2. 脚本和测试代码中可以使用 print()
3. 调试代码可以使用 print() 但应添加注释说明

返回 JSON 格式:
{
  "violations": [
    {"line": 42, "reason": "业务代码中使用 print() 输出"}
  ]
}

如果没有违规, 返回: {"violations": []}"""

    def _parse_ai_result(self, result: Dict) -> List[RuleViolation]:
        """解析 AI 返回结果"""
        violations = []
        logger_module = self.config.get('logger_module', 'logging')

        for item in result.get('violations', []):
            line_num = item.get('line', 0)
            reason = item.get('reason', '使用了 print() 进行输出')

            violations.append(RuleViolation(
                rule=self.name,
                message=reason,
                line=line_num,
                column=0,
                severity=Severity.WARNING,
                suggestion=f"建议使用 {logger_module} 进行日志记录"
            ))

        return violations

    def _fallback_check(self, file_path: str, content: str) -> List[RuleViolation]:
        """正则降级检查"""
        violations = []
        logger_module = self.config.get('logger_module', 'logging')

        # 检测 print() 调用
        print_pattern = r'\bprint\s*\('
        for line_num, line in enumerate(content.split('\n'), 1):
            if re.search(print_pattern, line):
                # 跳过注释
                if line.strip().startswith('#'):
                    continue

                violations.append(RuleViolation(
                    rule=self.name,
                    message="使用了 print() 进行输出",
                    line=line_num,
                    column=0,
                    severity=Severity.WARNING,
                    suggestion=f"建议使用 {logger_module} 进行日志记录"
                ))

        return violations


# =============================================================================
# 预制规则 4: 接口保护规则
# =============================================================================

class InterfaceProtectionRule(BaseRule):
    """接口保护规则 - Command Handler

    检查 Protected Interface 签名是否被未声明修改
    使用 AST 解析 + 签名持久化比对
    签名存储在对应 task 目录下
    """

    name = "interface_protection"
    layer = 3
    handler_type = "command"
    description = "检查 Protected Interface 签名是否被修改"

    # 签名文件名 (存储在 task 目录下)
    SIGNATURE_FILENAME = ".signatures.json"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._signatures: Dict[str, Dict] = {}
        self._task_dir: Optional[str] = None
        self._load_signatures()

    def _get_project_root(self) -> Path:
        """获取项目根目录"""
        cwd = os.getcwd()
        path = Path(cwd)
        for _ in range(5):
            if (path / ".git").exists() or (path / ".claude").exists():
                return path
            path = path.parent
        return Path(cwd)

    def _get_current_task_dir(self) -> Optional[str]:
        """获取当前 task 目录"""
        if self._task_dir:
            return self._task_dir

        project_root = self._get_project_root()
        current_task_file = project_root / ".claude" / "current-task.txt"

        if current_task_file.exists():
            try:
                task_path = current_task_file.read_text().strip()
                # 处理相对路径
                if not task_path.startswith('/'):
                    task_path = str(project_root / task_path)
                if os.path.isdir(task_path):
                    self._task_dir = task_path
                    return self._task_dir
            except IOError:
                pass

        return None

    def _get_signature_path(self) -> Optional[str]:
        """获取签名文件路径 (在 task 目录下)"""
        task_dir = self._get_current_task_dir()
        if task_dir:
            return os.path.join(task_dir, self.SIGNATURE_FILENAME)
        return None

    def _load_signatures(self) -> None:
        """加载历史签名"""
        sig_path = self._get_signature_path()
        if sig_path and os.path.exists(sig_path):
            try:
                with open(sig_path, 'r', encoding='utf-8') as f:
                    self._signatures = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._signatures = {}

    def _save_signatures(self) -> None:
        """持久化签名 (到 task 目录)"""
        sig_path = self._get_signature_path()
        if sig_path:
            with open(sig_path, 'w', encoding='utf-8') as f:
                json.dump(self._signatures, f, indent=2, ensure_ascii=False)

    def _extract_signatures(self, content: str) -> Dict[str, Dict]:
        """提取当前代码的函数/类签名"""
        signatures = {}

        # 使用 ASTUtils 解析
        tree = ASTUtils.parse(content)
        if not tree:
            return signatures

        # 提取函数签名
        for func in ASTUtils.find_functions(tree):
            params = [arg.arg for arg in func.args.args]
            return_type = ast.unparse(func.returns) if func.returns else None
            sig_str = f"{func.name}({', '.join(params)}) -> {return_type or 'None'}"
            signatures[f"func:{func.name}"] = {
                "type": "function",
                "name": func.name,
                "params": params,
                "return_type": return_type,
                "line": func.lineno,
                "signature": sig_str
            }

        # 提取类签名
        for cls in ASTUtils.find_classes(tree):
            methods = ASTUtils.get_class_methods(cls)
            sig_str = f"class {cls.name}({', '.join(methods)})"
            signatures[f"class:{cls.name}"] = {
                "type": "class",
                "name": cls.name,
                "methods": methods,
                "line": cls.lineno,
                "signature": sig_str
            }

        return signatures

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """检查 Protected Interface 签名变更"""
        violations = []

        protected_files = self.config.get('protected_files', [])
        if file_path not in protected_files:
            return violations

        protected_functions = self.config.get('protected_functions', [])
        protected_classes = self.config.get('protected_classes', [])

        # 提取当前签名
        current_sigs = self._extract_signatures(content)

        # 文件键 (用于持久化)
        file_key = file_path.replace("/", "__")

        # 获取历史签名
        historical_sigs = self._signatures.get(file_key, {})

        # 检查函数签名
        for func_name in protected_functions:
            sig_key = f"func:{func_name}"
            current = current_sigs.get(sig_key)

            if current is None:
                # 函数被删除
                violations.append(RuleViolation(
                    rule=self.name,
                    message=f"Protected Function '{func_name}' 被删除",
                    line=0,
                    column=0,
                    severity=Severity.ERROR,
                    suggestion="删除 Protected Interface 必须在 plan.md 中声明并获批准"
                ))
            elif sig_key in historical_sigs:
                historical = historical_sigs[sig_key]
                if current["signature"] != historical["signature"]:
                    # 签名变化
                    violations.append(RuleViolation(
                        rule=self.name,
                        message=f"Protected Function '{func_name}' 签名被修改",
                        line=current["line"],
                        column=0,
                        severity=Severity.ERROR,
                        suggestion=f"修改前: {historical['signature']}\n修改后: {current['signature']}\n修改 Protected Interface 前必须在 plan.md 中声明"
                    ))

        # 检查类签名
        for class_name in protected_classes:
            sig_key = f"class:{class_name}"
            current = current_sigs.get(sig_key)

            if current is None:
                # 类被删除
                violations.append(RuleViolation(
                    rule=self.name,
                    message=f"Protected Class '{class_name}' 被删除",
                    line=0,
                    column=0,
                    severity=Severity.ERROR,
                    suggestion="删除 Protected Interface 必须在 plan.md 中声明并获批准"
                ))
            elif sig_key in historical_sigs:
                historical = historical_sigs[sig_key]
                if current["signature"] != historical["signature"]:
                    # 签名变化 (方法列表变化)
                    violations.append(RuleViolation(
                        rule=self.name,
                        message=f"Protected Class '{class_name}' 签名被修改",
                        line=current["line"],
                        column=0,
                        severity=Severity.ERROR,
                        suggestion=f"修改前: {historical['signature']}\n修改后: {current['signature']}\n修改 Protected Interface 前必须在 plan.md 中声明"
                    ))

        # 如果没有违规，更新签名基线
        if not violations:
            self._signatures[file_key] = current_sigs
            self._save_signatures()

        return violations

    def update_baseline(self, file_path: str, content: str) -> None:
        """手动更新签名基线 (审批后调用)"""
        file_key = file_path.replace("/", "__")
        self._signatures[file_key] = self._extract_signatures(content)
        self._save_signatures()


# =============================================================================
# 预制规则注册表
# =============================================================================

PRESET_RULES = {
    "module_isolation": ModuleIsolationRule,
    "i18n_required": I18nRule,
    "logger_standard": LoggerRule,
    "interface_protection": InterfaceProtectionRule,
}


def get_preset_rule(name: str, config: Dict[str, Any] = None) -> Optional[BaseRule]:
    """获取预制规则实例

    Args:
        name: 规则名称
        config: 规则配置

    Returns:
        规则实例，不存在返回 None
    """
    rule_class = PRESET_RULES.get(name)
    if rule_class:
        return rule_class(config)
    return None


def list_preset_rules() -> List[str]:
    """列出所有可用的预制规则"""
    return list(PRESET_RULES.keys())
