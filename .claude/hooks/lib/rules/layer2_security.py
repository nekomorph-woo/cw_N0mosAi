"""
第二层规则: 安全检查
"""

import subprocess
import json
import os
from typing import List
from .base_rule import BaseRule, RuleViolation, Severity
from ..utils import create_temp_file


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

        # 检查 bandit 是否可用
        try:
            subprocess.run(["bandit", "--version"], capture_output=True, check=True)
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
                ["bandit", "-f", "json", "-ll", temp_file],
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
