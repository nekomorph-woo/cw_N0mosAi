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
import hashlib
import time
import ssl
import urllib.request
import urllib.error
from typing import List, Optional, Dict, Any
from .base_rule import BaseRule, RuleViolation, Severity


# =============================================================================
# Layer 3 基类
# =============================================================================

class Layer3Rule(BaseRule):
    """第三层业务规则基类"""

    layer = 3
    handler_type: str = "command"  # "command" / "prompt" / "agent"

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}


# =============================================================================
# AI Client - 轻量级 AI 调用客户端
# =============================================================================

class AIClient:
    """
    轻量级 AI 客户端 - 零配置设计

    环境变量 (优先级递减):
      API Key: ANTHROPIC_API_KEY > NOMOS_API_KEY > CLAUDE_API_KEY
      Base URL: ANTHROPIC_BASE_URL > NOMOS_API_BASE_URL
      Model: DEFAULT_HAIKU_MODEL > NOMOS_HAIKU_MODEL > 默认值
      Timeout: NOMOS_AI_TIMEOUT (默认 30 秒)
    """

    _instance = None
    _initialized = False

    # 默认配置
    DEFAULT_MODEL = "claude-3-5-haiku-20241022"
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 读取 API Key (四选一)
        self.api_key = (
            os.environ.get("ANTHROPIC_API_KEY") or
            os.environ.get("ANTHROPIC_AUTH_TOKEN") or  # 兼容某些客户端
            os.environ.get("NOMOS_API_KEY") or
            os.environ.get("CLAUDE_API_KEY")
        )

        # 读取 Base URL (可选)
        self.base_url = (
            os.environ.get("ANTHROPIC_BASE_URL") or
            os.environ.get("NOMOS_API_BASE_URL") or
            self.DEFAULT_BASE_URL
        )

        # 读取 Model (可选)
        self.model = (
            os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL") or
            os.environ.get("DEFAULT_HAIKU_MODEL") or
            os.environ.get("NOMOS_HAIKU_MODEL") or
            self.DEFAULT_MODEL
        )

        # 读取超时
        try:
            self.timeout = int(os.environ.get("NOMOS_AI_TIMEOUT", str(self.DEFAULT_TIMEOUT)))
        except ValueError:
            self.timeout = self.DEFAULT_TIMEOUT

        # 可用性标志
        self._available = self.api_key is not None

        # 简单内存缓存 (hash -> result)
        self._cache: Dict[str, Dict] = {}
        self._cache_max_size = 100

        self._initialized = True

    @property
    def available(self) -> bool:
        """AI 服务是否可用"""
        return self._available

    def call(self, prompt: str, content: str) -> Optional[Dict]:
        """
        调用 AI 进行判断 (带重试机制)

        Args:
            prompt: 系统提示词
            content: 待分析的代码内容

        Returns:
            解析后的 JSON 结果, 或 None (调用失败时)
        """
        if not self._available:
            return None

        # 检查缓存
        cache_key = hashlib.md5(f"{prompt}:{content}".encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 构建请求
        full_prompt = f"{prompt}\n\n---\n代码:\n```\n{content}\n```"

        request_body = {
            "model": self.model,
            "max_tokens": 512,
            "messages": [{"role": "user", "content": full_prompt}]
        }

        url = f"{self.base_url.rstrip('/')}/v1/messages"

        # 重试机制
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                result = self._make_request(url, request_body)

                # 尝试解析 JSON
                try:
                    parsed = json.loads(result)
                except json.JSONDecodeError:
                    # 尝试提取 markdown 代码块中的 JSON
                    import re as _re
                    json_match = _re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            parsed = {"raw_response": result, "violations": []}
                    else:
                        # AI 返回非 JSON, 包装成标准格式
                        parsed = {"raw_response": result, "violations": []}

                # 写入缓存
                self._cache[cache_key] = parsed
                if len(self._cache) > self._cache_max_size:
                    # 简单 LRU: 清空一半
                    keys = list(self._cache.keys())
                    for k in keys[:len(keys)//2]:
                        del self._cache[k]

                return parsed

            except (urllib.error.URLError, urllib.error.HTTPError,
                    KeyError, TimeoutError, Exception) as e:
                last_error = e
                # 重试前等待 (指数退避)
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(1 * (attempt + 1))
                continue

        # 所有重试失败
        return None

    def _make_request(self, url: str, body: Dict) -> str:
        """发起 HTTP 请求"""
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            method="POST"
        )

        # 创建 SSL 上下文 (处理证书验证问题)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=self.timeout, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result["content"][0]["text"]


# =============================================================================
# Prompt Handler 基类
# =============================================================================

class PromptHandler(Layer3Rule):
    """
    Prompt Handler 基类 - 支持智能语义判断

    子类需要实现:
      - ai_prompt: 返回 AI 提示词
      - parse_ai_result(): 解析 AI 返回结果
      - fallback_check(): 正则降级检查
    """

    handler_type = "prompt"

    # 共享的 AI 客户端 (单例)
    _ai_client: Optional[AIClient] = None

    @classmethod
    def get_ai_client(cls) -> AIClient:
        """获取共享 AI 客户端"""
        if cls._ai_client is None:
            cls._ai_client = AIClient()
        return cls._ai_client

    @property
    def ai_prompt(self) -> str:
        """子类实现: 返回 AI 提示词"""
        raise NotImplementedError

    def parse_ai_result(self, result: Dict, file_path: str,
                        content: str) -> List[RuleViolation]:
        """子类实现: 解析 AI 返回结果"""
        raise NotImplementedError

    def fallback_check(self, file_path: str,
                       content: str) -> List[RuleViolation]:
        """子类实现: 正则降级检查"""
        return []

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """智能检查: AI 优先, 正则降级"""

        # 快速预检: 确定性场景直接返回
        quick_result = self._quick_check(file_path, content)
        if quick_result is not None:
            return quick_result

        # 尝试 AI 判断
        ai_client = self.get_ai_client()
        if ai_client.available:
            ai_result = ai_client.call(self.ai_prompt, content)
            if ai_result is not None:
                return self.parse_ai_result(ai_result, file_path, content)

        # 降级到正则
        return self.fallback_check(file_path, content)

    def _quick_check(self, file_path: str,
                     content: str) -> Optional[List[RuleViolation]]:
        """
        快速预检 - 确定性场景跳过 AI

        返回:
          - 非空列表: 有违规
          - 空列表: 无违规
          - None: 不确定, 需要 AI 判断
        """
        return None  # 默认不确定


# =============================================================================
# 具体规则实现
# =============================================================================

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


class I18nRule(PromptHandler):
    """国际化规则 - 智能版

    检查 UI 相关代码是否使用 i18n
    """

    name = "i18n_required"
    description = "检查 UI 代码是否使用 i18n"

    @property
    def ai_prompt(self) -> str:
        return """你是代码审查专家。检查代码中的硬编码字符串。

规则:
1. 用户可见的 UI 文本必须使用 i18n 函数包装
2. 日志/调试信息可以硬编码
3. 错误消息应该使用 i18n
4. 注释中的字符串不需要处理

返回 JSON 格式:
{
  "violations": [
    {"line": 10, "text": "Hello World", "reason": "UI文本未国际化"}
  ]
}

如果没有违规, 返回: {"violations": []}"""

    def _quick_check(self, file_path: str,
                     content: str) -> Optional[List[RuleViolation]]:
        """快速预检: 没有字符串字面量则直接通过"""
        # 检查文件是否在目标目录中
        target_dirs = self.config.get('target_dirs', [])
        if target_dirs and not any(file_path.startswith(d) for d in target_dirs):
            return []  # 不在目标目录, 直接通过

        # 检查是否在排除模式中
        exclude_patterns = self.config.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if re.match(pattern.replace('*', '.*'), os.path.basename(file_path)):
                return []  # 排除的文件, 直接通过

        # 没有长字符串字面量, 直接通过
        if not re.search(r'["\'][^"\']{10,}["\']', content):
            return []

        return None  # 需要 AI 判断

    def parse_ai_result(self, result: Dict, file_path: str,
                        content: str) -> List[RuleViolation]:
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

    def fallback_check(self, file_path: str,
                       content: str) -> List[RuleViolation]:
        """正则降级 (原有逻辑)"""
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


class LoggerRule(PromptHandler):
    """Logger 规范规则 - 智能版

    检查是否使用标准 logger 而非 print
    """

    name = "logger_standard"
    description = "检查是否使用标准 logger"

    @property
    def ai_prompt(self) -> str:
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

    def _quick_check(self, file_path: str,
                     content: str) -> Optional[List[RuleViolation]]:
        """快速预检: 没有 print() 则直接通过"""
        # 检查是否在允许 print 的目录中
        allow_print_in = self.config.get('allow_print_in', [])
        if any(file_path.startswith(d) for d in allow_print_in):
            return []  # 允许的目录, 直接通过

        # 没有 print() 调用, 直接通过
        if not re.search(r'\bprint\s*\(', content):
            return []

        return None  # 需要 AI 判断

    def parse_ai_result(self, result: Dict, file_path: str,
                        content: str) -> List[RuleViolation]:
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

    def fallback_check(self, file_path: str,
                       content: str) -> List[RuleViolation]:
        """正则降级 (原有逻辑)"""
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
                        rule=self.name,
                        message=f"Protected Function '{node.name}' 被修改",
                        line=node.lineno,
                        column=0,
                        severity=Severity.ERROR,
                        suggestion="修改 Protected Interface 前必须在 plan.md 中声明"
                    ))

            # 检查类定义
            if isinstance(node, ast.ClassDef):
                if node.name in protected_classes:
                    violations.append(RuleViolation(
                        rule=self.name,
                        message=f"Protected Class '{node.name}' 被修改",
                        line=node.lineno,
                        column=0,
                        severity=Severity.ERROR,
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
