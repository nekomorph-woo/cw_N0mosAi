"""
规则上下文模块 - 提供规则执行上下文

l3_foundation 基础能力层核心模块
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List


class RuleContext:
    """规则上下文 - 提供当前任务和项目信息"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化规则上下文"""
        if self._initialized:
            return

        self._task_dir: Optional[str] = None
        self._project_root: Optional[Path] = None
        self._plan_content: Optional[str] = None

        self._initialized = True

    def reset(self):
        """重置上下文 (用于测试或切换任务)"""
        self._task_dir = None
        self._project_root = None
        self._plan_content = None

    @property
    def task_dir(self) -> Optional[str]:
        """获取当前 task 目录"""
        if self._task_dir:
            return self._task_dir

        project_root = self.project_root
        if not project_root:
            return None

        current_task_file = project_root / ".claude" / "current-task.txt"
        if current_task_file.exists():
            try:
                task_path = current_task_file.read_text().strip()
                if not task_path.startswith('/'):
                    task_path = str(project_root / task_path)
                if os.path.isdir(task_path):
                    self._task_dir = task_path
                    return self._task_dir
            except IOError:
                pass

        return None

    @property
    def project_root(self) -> Optional[Path]:
        """获取项目根目录"""
        if self._project_root:
            return self._project_root

        cwd = os.getcwd()
        path = Path(cwd)
        for _ in range(5):
            if (path / ".git").exists() or (path / ".claude").exists():
                self._project_root = path
                return self._project_root
            path = path.parent

        return Path(cwd)

    @property
    def plan_content(self) -> Optional[str]:
        """获取 plan.md 内容"""
        if self._plan_content:
            return self._plan_content

        task_dir = self.task_dir
        if not task_dir:
            return None

        plan_file = Path(task_dir) / "plan.md"
        if plan_file.exists():
            try:
                self._plan_content = plan_file.read_text(encoding='utf-8')
                return self._plan_content
            except IOError:
                pass

        return None

    @property
    def task_id(self) -> Optional[str]:
        """获取当前 task ID"""
        task_dir = self.task_dir
        if task_dir:
            return Path(task_dir).name
        return None

    @property
    def rules_dir(self) -> Optional[str]:
        """获取规则目录路径"""
        task_dir = self.task_dir
        if task_dir:
            return os.path.join(task_dir, "rules")
        return None

    @property
    def signatures_file(self) -> Optional[str]:
        """获取签名文件路径"""
        task_dir = self.task_dir
        if task_dir:
            return os.path.join(task_dir, ".signatures.json")
        return None

    def get_plan_metadata(self) -> Dict[str, Any]:
        """
        获取 plan.md 的元数据

        Returns:
            元数据字典 (从 YAML Frontmatter 解析)
        """
        plan_content = self.plan_content
        if not plan_content:
            return {}

        # 提取 YAML Frontmatter
        if not plan_content.startswith('---'):
            return {}

        parts = plan_content.split('---', 2)
        if len(parts) < 3:
            return {}

        try:
            import yaml
            frontmatter = yaml.safe_load(parts[1])
            return frontmatter if frontmatter else {}
        except Exception:
            return {}

    def get_business_rules(self) -> List[Dict[str, Any]]:
        """
        从 plan.md 提取业务规则

        Returns:
            业务规则列表
        """
        plan_content = self.plan_content
        if not plan_content:
            return []

        # 查找业务规则章节
        lines = plan_content.split('\n')
        rules_start = -1

        for i, line in enumerate(lines):
            if line.strip() == "## 业务规则":
                rules_start = i
                break

        if rules_start == -1:
            return []

        # 提取业务规则内容 (到下一个二级标题或文件结束)
        rules_lines = []
        for i in range(rules_start + 1, len(lines)):
            if lines[i].startswith("## ") and i > rules_start + 1:
                break
            rules_lines.append(lines[i])

        rules_text = '\n'.join(rules_lines)

        # 解析规则 (支持多种格式)
        rules = []
        current_rule = {}

        for line in rules_lines:
            line = line.strip()
            if not line:
                if current_rule:
                    rules.append(current_rule)
                    current_rule = {}
                continue

            # 格式: "1. 规则描述"
            if line[0].isdigit() and ". " in line:
                if current_rule:
                    rules.append(current_rule)
                parts = line.split(". ", 1)
                current_rule = {"index": int(parts[0]), "description": parts[1]}

            # 格式: "- Handler: command/prompt"
            elif line.startswith("- Handler:") or line.startswith("Handler:"):
                handler_type = line.split(":", 1)[1].strip().lower()
                current_rule["handler_type"] = handler_type

            # 格式: "- Severity: error/warning/info"
            elif line.startswith("- Severity:") or line.startswith("Severity:"):
                severity = line.split(":", 1)[1].strip().lower()
                current_rule["severity"] = severity

            # 格式: "- Files: src/**/*.py"
            elif line.startswith("- Files:") or line.startswith("Files:"):
                files = line.split(":", 1)[1].strip()
                current_rule["target_files"] = files

        if current_rule:
            rules.append(current_rule)

        return rules
