"""
第二层规则: 安全检查
"""

import subprocess
import json
import os
import sys
from typing import List, Optional
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


class BanditRule(BaseRule):
    """Bandit Python 安全扫描封装"""

    name = "bandit"
    layer = 2
    description = "Python 安全漏洞扫描 (Bandit)"
    supported_languages = ["python"]

    # 关注的安全问题类别
    SEVERITY_MAP = {
        "HIGH": Severity.ERROR,
        "MEDIUM": Severity.WARNING,
        "LOW": Severity.INFO
    }

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """
        调用 bandit -f json 并解析输出

        实现要点:
        1. 将 content 写入临时文件
        2. 运行 bandit -f json -ll (只报告 MEDIUM+)
        3. 解析 JSON 输出
        4. 映射严重程度
        """
        violations = []

        # 查找 bandit 可执行文件
        bandit_exe = _find_executable("bandit")

        # 检查 bandit 是否可用
        try:
            subprocess.run([bandit_exe, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return [RuleViolation(
                rule="bandit:not_found",
                message="Bandit 未安装，请运行: pip install bandit",
                line=0,
                column=0,
                severity=Severity.WARNING,
                suggestion="pip install bandit",
                source="layer2"
            )]

        # 写入临时文件
        temp_file = create_temp_file(content, suffix=".py")

        try:
            # 运行 bandit
            result = subprocess.run(
                [bandit_exe, "-f", "json", "-ll", temp_file],
                capture_output=True,
                text=True
            )

            # 解析 JSON 输出
            if result.stdout:
                try:
                    bandit_output = json.loads(result.stdout)
                    for issue in bandit_output.get('results', []):
                        severity_str = issue.get('issue_severity', 'LOW')
                        severity = self.SEVERITY_MAP.get(severity_str, Severity.INFO)

                        violations.append(RuleViolation(
                            rule=f"bandit:{issue.get('test_id', 'unknown')}",
                            message=issue.get('issue_text', ''),
                            line=issue.get('line_number', 0),
                            column=0,  # Bandit 不提供列号
                            severity=severity,
                            suggestion=self._get_suggestion(issue.get('test_id', '')),
                            source="layer2"
                        ))
                except json.JSONDecodeError:
                    pass

        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return violations

    def _get_suggestion(self, test_id: str) -> str:
        """根据测试 ID 提供修复建议"""
        suggestions = {
            "B105": "使用环境变量或配置文件存储密钥",
            "B106": "使用环境变量或配置文件存储密码",
            "B107": "使用环境变量或配置文件存储敏感信息",
            "B201": "避免使用 flask.debug=True",
            "B301": "避免使用 pickle，考虑使用 json",
            "B302": "避免使用 marshal",
            "B303": "避免使用不安全的 MD5/SHA1",
            "B304": "避免使用不安全的加密算法",
            "B305": "避免使用不安全的加密模式",
            "B306": "避免使用 tempfile.mktemp",
            "B307": "使用 defusedxml 替代标准 xml 库",
            "B308": "避免使用 mark_safe",
            "B309": "避免使用 HTTPSConnection 时禁用证书验证",
            "B310": "避免使用 urllib.urlopen",
            "B311": "使用 secrets 模块替代 random",
            "B312": "避免使用 telnetlib",
            "B313": "避免使用不安全的 XML 解析器",
            "B314": "避免使用不安全的 XML 解析器",
            "B315": "避免使用不安全的 XML 解析器",
            "B316": "避免使用不安全的 XML 解析器",
            "B317": "避免使用不安全的 XML 解析器",
            "B318": "避免使用不安全的 XML 解析器",
            "B319": "避免使用不安全的 XML 解析器",
            "B320": "避免使用不安全的 XML 解析器",
            "B321": "避免使用 FTP",
            "B322": "避免使用 input() 函数",
            "B323": "避免使用不安全的随机数生成器",
            "B324": "避免使用弱哈希算法",
            "B325": "避免使用 tempfile.mktemp",
            "B401": "避免导入 telnetlib",
            "B402": "避免导入 ftplib",
            "B403": "避免导入 pickle",
            "B404": "避免导入 subprocess",
            "B405": "避免导入 xml.etree",
            "B406": "避免导入 xml.sax",
            "B407": "避免导入 xml.expat",
            "B408": "避免导入 xml.minidom",
            "B409": "避免导入 xml.pulldom",
            "B410": "避免导入 lxml",
            "B411": "避免导入 xmlrpclib",
            "B412": "避免导入 httpoxy",
            "B413": "避免导入 pycrypto",
            "B501": "避免使用不安全的证书验证",
            "B502": "避免使用不安全的 SSL/TLS 版本",
            "B503": "避免使用不安全的加密算法",
            "B504": "避免使用不安全的 SSL/TLS 配置",
            "B505": "避免使用弱加密密钥",
            "B506": "避免使用不安全的 YAML 加载",
            "B507": "避免使用不安全的 SSH 配置",
            "B601": "避免使用 shell=True",
            "B602": "避免使用 shell=True",
            "B603": "避免使用 subprocess 时不验证输入",
            "B604": "避免使用 shell=True",
            "B605": "避免使用 shell=True",
            "B606": "避免使用 shell=True",
            "B607": "避免使用部分路径执行命令",
            "B608": "避免 SQL 注入",
            "B609": "避免使用通配符注入",
            "B610": "避免 SQL 注入",
            "B611": "避免 SQL 注入",
            "B701": "避免使用 jinja2.autoescape=False",
            "B702": "避免使用 mako.autoescape=False",
            "B703": "避免使用 django.mark_safe",
        }

        return suggestions.get(test_id, "请参考 Bandit 文档")


class ESLintSecurityRule(BaseRule):
    """ESLint Security 插件封装 (JS/TS 安全检查)

    使用 Node.js 脚本调用 ESLint Linter API，避免 CLI 路径限制
    """

    name = "eslint-security"
    layer = 2
    description = "JavaScript/TypeScript 安全漏洞扫描 (ESLint Security)"
    supported_languages = ["javascript", "typescript"]

    # 严重程度映射
    SEVERITY_MAP = {
        2: Severity.ERROR,    # ESLint error
        1: Severity.WARNING,  # ESLint warn
    }

    # ESLint 检查脚本 (使用 Linter API with eslintrc mode)
    ESLINT_SCRIPT = '''
const { Linter } = require("eslint");
const securityPlugin = require("eslint-plugin-security");

// 使用 eslintrc 模式以支持 defineRule
const linter = new Linter({ configType: "eslintrc" });

// 注册 security 插件规则
Object.entries(securityPlugin.rules).forEach(([name, rule]) => {
    linter.defineRule(`security/${name}`, rule);
});

// 安全规则配置
const config = {
    rules: {
        "security/detect-eval-with-expression": "error",
        "security/detect-non-literal-require": "error",
        "security/detect-non-literal-fs-filename": "warn",
        "security/detect-non-literal-regexp": "warn",
        "security/detect-unsafe-regex": "error",
        "security/detect-object-injection": "warn",
        "security/detect-child-process": "warn",
        "security/detect-new-buffer": "error",
        "security/detect-pseudoRandomBytes": "error",
        "security/detect-possible-timing-attacks": "warn",
        "security/detect-buffer-noassert": "warn",
        "security/detect-disable-mustache-escape": "error",
    }
};

// node -e 时，argv[1] 是第一个参数
const code = process.argv[1] || "";

const messages = linter.verify(code, config);
console.log(JSON.stringify(messages));
'''

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """调用 Node.js ESLint API 执行安全检查"""
        violations = []

        # 检查 node 和 eslint-plugin-security 是否可用
        if not self._check_dependencies():
            return [RuleViolation(
                rule="eslint-security:not_found",
                message="ESLint 或 eslint-plugin-security 未安装",
                line=0,
                column=0,
                severity=Severity.WARNING,
                suggestion="npm install eslint eslint-plugin-security",
                source="layer2"
            )]

        try:
            # 运行 Node.js 检查脚本
            # node -e "script" <content> <file_path>
            # process.argv[2] = content, process.argv[3] = file_path
            result = subprocess.run(
                ["node", "-e", self.ESLINT_SCRIPT, content],
                capture_output=True,
                text=True,
                cwd=_get_project_root() or os.getcwd()
            )

            if result.stdout:
                try:
                    messages = json.loads(result.stdout)
                    for msg in messages:
                        rule_id = msg.get('ruleId', '')
                        if not rule_id:
                            continue

                        severity_int = msg.get('severity', 1)
                        severity = self.SEVERITY_MAP.get(severity_int, Severity.WARNING)

                        violations.append(RuleViolation(
                            rule=f"eslint:{rule_id}",
                            message=msg.get('message', ''),
                            line=msg.get('line', 0),
                            column=msg.get('column', 0),
                            severity=severity,
                            suggestion=self._get_suggestion(rule_id),
                            source="layer2"
                        ))
                except json.JSONDecodeError:
                    pass

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # 执行失败，返回警告但不阻塞
            pass

        return violations

    def _check_dependencies(self) -> bool:
        """检查 Node.js 和 eslint-plugin-security 是否可用"""
        try:
            # 检查 node
            result = subprocess.run(
                ["node", "-e", "require('eslint-plugin-security')"],
                capture_output=True,
                text=True,
                cwd=_get_project_root() or os.getcwd()
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _get_suggestion(self, rule_id: str) -> str:
        """根据规则 ID 提供修复建议"""
        suggestions = {
            "security/detect-eval-with-expression": "避免使用动态 eval()，考虑使用更安全的替代方案",
            "security/detect-non-literal-require": "避免动态 require()，可能导致代码注入",
            "security/detect-object-injection": "验证对象属性访问的键值，防止原型污染",
            "security/detect-unsafe-regex": "正则表达式可能导致 ReDoS 攻击，优化正则表达式",
            "security/detect-non-literal-regexp": "避免使用动态构建的正则表达式",
            "security/detect-non-literal-fs-filename": "验证文件路径输入，防止路径遍历攻击",
            "security/detect-child-process": "验证子进程命令参数，防止命令注入",
            "security/detect-new-buffer": "使用 Buffer.from() 替代 new Buffer()",
            "security/detect-buffer-noassert": "Buffer 操作应启用边界检查",
            "security/detect-pseudoRandomBytes": "使用 crypto.randomBytes() 替代伪随机数生成器",
            "security/detect-possible-timing-attacks": "使用恒定时间比较函数比较敏感数据",
            "security/detect-disable-mustache-escape": "不要禁用模板引擎的 HTML 转义",
        }
        return suggestions.get(rule_id, "请参考 ESLint Security 文档")


class TreeSitterSecurityRule(BaseRule):
    """Tree-sitter 通用安全检测 (Tier 2 语言)

    使用 AST 分析检测跨语言的安全问题模式，无需安装额外工具。
    适用于 Go, Java, Rust, Ruby, PHP 等语言。
    """

    name = "tree-sitter-security"
    layer = 2
    description = "通用安全模式检测 (Tree-sitter AST)"
    # 支持 Tier 2 语言 + Python/JS (作为原生工具的补充)
    supported_languages = [
        "go", "java", "rust", "c", "cpp", "c_sharp",
        "ruby", "php", "swift", "kotlin", "scala",
        "lua", "perl", "r",
        # 也支持 Python/JS，但原生工具优先
        "python", "javascript", "typescript"
    ]

    # 危险函数调用模式 (函数名 -> 安全建议)
    DANGEROUS_FUNCTIONS = {
        # 代码执行
        "eval": "避免动态代码执行，可能导致代码注入",
        "exec": "避免动态代码执行，可能导致代码注入",
        "execfile": "避免动态代码执行，可能导致代码注入",
        "compile": "注意动态编译的安全性",
        # 命令执行
        "system": "避免直接执行系统命令，验证输入",
        "popen": "避免直接执行系统命令，验证输入",
        "subprocess": "验证命令参数，使用 shell=False",
        "shell_exec": "避免直接执行 shell 命令",
        "passthru": "避免直接执行系统命令",
        "Runtime.getRuntime": "避免直接执行系统命令",
        "os/exec": "验证命令参数",
        "Command::new": "验证命令参数",
        # 文件操作
        "unlink": "验证文件路径，防止路径遍历",
        "remove": "验证文件路径，防止路径遍历",
        "delete": "验证文件路径，防止路径遍历",
        "rmdir": "验证文件路径，防止路径遍历",
    }

    # 硬编码密钥正则模式 (支持多种赋值语法: =, :=, ->, :)
    SECRET_PATTERNS = [
        (r'(?i)(password|passwd|pwd)\s*:?=\s*["\'][^"\']{4,}["\']', "硬编码密码"),
        (r'(?i)(api_key|apikey|api-key)\s*:?=\s*["\'][^"\']{8,}["\']', "硬编码 API Key"),
        (r'(?i)(secret|secret_key)\s*:?=\s*["\'][^"\']{8,}["\']', "硬编码密钥"),
        (r'(?i)(token|access_token)\s*:?=\s*["\'][^"\']{8,}["\']', "硬编码 Token"),
        (r'(?i)(private_key|privatekey)\s*:?=\s*["\'][^"\']{20,}["\']', "硬编码私钥"),
        (r'["\']sk-[a-zA-Z0-9]{20,}["\']', "疑似 OpenAI API Key"),
        (r'["\']AKIA[0-9A-Z]{16}["\']', "疑似 AWS Access Key"),
        (r'["\']ghp_[a-zA-Z0-9]{36}["\']', "疑似 GitHub Token"),
    ]

    # SQL 注入模式
    SQL_INJECTION_PATTERNS = [
        (r'["\']\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+.*["\'].*\+', "SQL 字符串拼接"),
        (r'["\']\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+.*["\'].*format\(', "SQL 格式化字符串"),
        (r'["\']\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+.*["\'].*\%', "SQL 格式化字符串"),
        (r'f["\'].*\{.*\}.*["\'].*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b', "SQL f-string 注入"),
    ]

    def check(self, file_path: str, content: str) -> List[RuleViolation]:
        """执行安全检查"""
        violations = []

        # 1. 检测硬编码密钥 (正则匹配)
        violations.extend(self._check_secrets(content))

        # 2. 检测 SQL 注入模式 (正则匹配)
        violations.extend(self._check_sql_injection(content))

        # 3. 检测危险函数调用 (Tree-sitter AST 或 文本匹配)
        violations.extend(self._check_dangerous_calls(content, file_path))

        return violations

    def _check_secrets(self, content: str) -> List[RuleViolation]:
        """检测硬编码密钥"""
        import re
        violations = []
        lines = content.split('\n')

        for pattern, desc in self.SECRET_PATTERNS:
            for i, line in enumerate(lines, 1):
                # 跳过注释行
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('*'):
                    continue

                if re.search(pattern, line):
                    violations.append(RuleViolation(
                        rule="tree-sitter:hardcoded-secret",
                        message=f"{desc} 检测到敏感信息",
                        line=i,
                        column=0,
                        severity=Severity.ERROR,
                        suggestion="使用环境变量或密钥管理服务存储敏感信息",
                        source="layer2"
                    ))
                    break  # 每种模式每行只报告一次

        return violations

    def _check_sql_injection(self, content: str) -> List[RuleViolation]:
        """检测 SQL 注入模式"""
        import re
        violations = []
        lines = content.split('\n')

        for pattern, desc in self.SQL_INJECTION_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(RuleViolation(
                        rule="tree-sitter:sql-injection",
                        message=f"{desc} 可能导致 SQL 注入",
                        line=i,
                        column=0,
                        severity=Severity.ERROR,
                        suggestion="使用参数化查询或 ORM",
                        source="layer2"
                    ))
                    break

        return violations

    def _check_dangerous_calls(self, content: str, file_path: str) -> List[RuleViolation]:
        """检测危险函数调用"""
        violations = []

        # 尝试使用 Tree-sitter 解析
        ast_result = self._parse_with_tree_sitter(content, file_path)

        if ast_result:
            # 使用 AST 检测
            violations.extend(self._find_dangerous_calls_in_ast(ast_result, content))
        else:
            # 降级到文本匹配
            violations.extend(self._find_dangerous_calls_text(content))

        return violations

    def _parse_with_tree_sitter(self, content: str, file_path: str):
        """使用 Tree-sitter 解析代码"""
        try:
            from ..multilang import LanguageDetector, TreeSitterEngine, Language

            detector = LanguageDetector()
            language = detector.detect(Path(file_path))

            engine = TreeSitterEngine()
            if not engine.is_language_supported(language):
                return None

            ok, _ = engine.check_syntax(content, language)
            if not ok:
                return None

            # 返回解析树用于分析
            return {
                'engine': engine,
                'language': language,
                'content': content
            }
        except Exception:
            return None

    def _find_dangerous_calls_in_ast(self, ast_result: dict, content: str) -> List[RuleViolation]:
        """在 AST 中查找危险调用"""
        violations = []
        lines = content.split('\n')

        try:
            from tree_sitter import Parser

            engine = ast_result['engine']
            language = ast_result['language']

            if language not in engine._languages_available:
                return violations

            ts_lang = engine._languages_available[language]
            parser = Parser(ts_lang)
            tree = parser.parse(content.encode('utf-8'))
            root = tree.root_node

            # 遍历 AST 查找调用表达式
            self._traverse_for_calls(root, lines, violations)

        except Exception:
            pass

        return violations

    def _traverse_for_calls(self, node, lines: List[str], violations: List[RuleViolation]):
        """递归遍历 AST 查找函数调用"""
        # 检查是否是调用节点
        node_type = node.type

        # 不同语言的调用表达式类型
        call_types = [
            'call_expression', 'function_call', 'method_call',
            'call', 'invocation_expression', 'method_invocation'
        ]

        if node_type in call_types:
            # 提取函数名
            func_name = self._extract_function_name(node)
            if func_name and func_name in self.DANGEROUS_FUNCTIONS:
                line = node.start_point[0] + 1
                violations.append(RuleViolation(
                    rule=f"tree-sitter:dangerous-call",
                    message=f"危险函数调用: {func_name}()",
                    line=line,
                    column=node.start_point[1] + 1,
                    severity=Severity.WARNING,
                    suggestion=self.DANGEROUS_FUNCTIONS[func_name],
                    source="layer2"
                ))

        # 递归检查子节点
        for child in node.children:
            self._traverse_for_calls(child, lines, violations)

    def _extract_function_name(self, node) -> Optional[str]:
        """从调用节点提取函数名"""
        # 获取节点的文本
        try:
            text = node.text.decode('utf-8') if hasattr(node, 'text') else ''
        except Exception:
            return None

        # 查找第一个子节点（通常是函数名）
        for child in node.children:
            child_type = child.type
            # 标识符类型
            if child_type in ['identifier', 'simple_identifier', 'name', 'IDENTIFIER']:
                try:
                    return child.text.decode('utf-8')
                except Exception:
                    pass
            # 成员访问 (如 Runtime.getRuntime)
            elif child_type in ['member_expression', 'field_access', 'scoped_identifier']:
                try:
                    return child.text.decode('utf-8')
                except Exception:
                    pass

        # 回退：从文本提取
        import re
        match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\(', text)
        if match:
            return match.group(1)

        return None

    def _find_dangerous_calls_text(self, content: str) -> List[RuleViolation]:
        """文本模式匹配危险调用（降级方案）"""
        import re
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # 跳过注释
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue

            for func_name, suggestion in self.DANGEROUS_FUNCTIONS.items():
                # 匹配函数调用模式
                pattern = rf'\b{re.escape(func_name)}\s*\('
                if re.search(pattern, line):
                    violations.append(RuleViolation(
                        rule="tree-sitter:dangerous-call",
                        message=f"危险函数调用: {func_name}()",
                        line=i,
                        column=0,
                        severity=Severity.WARNING,
                        suggestion=suggestion,
                        source="layer2"
                    ))

        return violations


def _get_project_root() -> str:
    """获取项目根目录"""
    cwd = os.getcwd()
    # 向上查找包含 package.json 或 .venv 的目录
    current = cwd
    for _ in range(5):
        if os.path.exists(os.path.join(current, 'package.json')):
            return current
        if os.path.exists(os.path.join(current, '.venv')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return cwd
