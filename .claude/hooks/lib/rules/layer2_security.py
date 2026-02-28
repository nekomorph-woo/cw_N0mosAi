"""
第二层规则: 安全检查
"""

import subprocess
import json
import os
import sys
from typing import List
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
