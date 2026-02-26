"""
三级豁免引擎 (Exemption Engine)

支持行级、文件级和规则级三种豁免机制，精细化管理 Linter 误报
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import yaml


@dataclass
class Exemption:
    """豁免规则"""
    rule_id: str
    level: str  # "line" | "file" | "rule"
    reason: Optional[str] = None
    expires: Optional[datetime] = None


class ExemptionEngine:
    """三级 Linter 误报豁免引擎"""

    def __init__(self, ignore_yml_path: Optional[Path] = None):
        """初始化豁免引擎

        Args:
            ignore_yml_path: ignore.yml 配置文件路径
        """
        self._rule_exemptions: List[Exemption] = []
        if ignore_yml_path and ignore_yml_path.exists():
            self._load_rule_exemptions(ignore_yml_path)

    def is_exempted(self, rule_id: str, file_path: Path, line: int,
                    source_line: str) -> bool:
        """检查某条 Lint 结果是否被豁免

        Args:
            rule_id: 规则 ID
            file_path: 文件路径
            line: 行号
            source_line: 源代码行

        Returns:
            是否被豁免
        """
        # Level 1: 行级豁免 — # noqa: RF001
        if self._check_line_exemption(rule_id, source_line):
            return True

        # Level 2: 文件级豁免 — # nomos-ignore: RF001, RF002
        if self._check_file_exemption(rule_id, file_path):
            return True

        # Level 3: 规则级豁免 — ignore.yml (含过期时间)
        if self._check_rule_exemption(rule_id):
            return True

        return False

    def _check_line_exemption(self, rule_id: str, source_line: str) -> bool:
        """检查行级豁免: # noqa: RF001

        Args:
            rule_id: 规则 ID
            source_line: 源代码行

        Returns:
            是否被豁免
        """
        match = re.search(r"#\s*noqa:\s*([\w,\s-]+)", source_line)
        if match:
            exempted_rules = [r.strip() for r in match.group(1).split(",")]
            return rule_id in exempted_rules
        return False

    def _check_file_exemption(self, rule_id: str, file_path: Path) -> bool:
        """检查文件级豁免: # nomos-ignore: RF001, RF002

        Args:
            rule_id: 规则 ID
            file_path: 文件路径

        Returns:
            是否被豁免
        """
        try:
            first_lines = file_path.read_text(encoding='utf-8').splitlines()[:5]
            for line in first_lines:
                match = re.search(r"#\s*nomos-ignore:\s*([\w,\s-]+)", line)
                if match:
                    exempted = [r.strip() for r in match.group(1).split(",")]
                    if rule_id in exempted:
                        return True
        except (OSError, UnicodeDecodeError):
            pass
        return False

    def _check_rule_exemption(self, rule_id: str) -> bool:
        """检查规则级豁免 (ignore.yml，含过期时间)

        Args:
            rule_id: 规则 ID

        Returns:
            是否被豁免
        """
        now = datetime.now()
        for ex in self._rule_exemptions:
            if ex.rule_id == rule_id:
                if ex.expires and ex.expires < now:
                    continue  # 已过期，不豁免
                return True
        return False

    def _load_rule_exemptions(self, path: Path) -> None:
        """从 ignore.yml 加载规则级豁免

        Args:
            path: ignore.yml 文件路径
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config or 'exemptions' not in config:
                return

            for item in config['exemptions']:
                rule_id = item.get('rule_id')
                if not rule_id:
                    continue

                expires = None
                if 'expires' in item:
                    try:
                        expires = datetime.fromisoformat(item['expires'])
                    except ValueError:
                        pass

                self._rule_exemptions.append(Exemption(
                    rule_id=rule_id,
                    level="rule",
                    reason=item.get('reason'),
                    expires=expires
                ))

        except (yaml.YAMLError, OSError):
            pass
