"""
Git 集成管理器
处理分支创建、commit 和 PR 生成
"""

import subprocess
import os
import re
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


class GitManager:
    """Git 集成管理器"""

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化 Git 管理器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or os.getcwd())

    def create_branch(self, task_id: str, task_name: str, branch_type: str = "feat") -> str:
        """
        创建任务分支

        Args:
            task_id: 任务 ID (如 t1)
            task_name: 任务名称
            branch_type: 分支类型 (feat/fix/refactor/test/docs)

        Returns:
            分支名称
        """
        # 生成分支名: feat/YYYY-MM-DD-task-name
        date_str = datetime.now().strftime("%Y-%m-%d")
        branch_name = f"{branch_type}/{date_str}-{task_name}"

        # 检查分支是否已存在
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            cwd=self.project_root,
            capture_output=True
        )

        if result.returncode == 0:
            # 分支已存在，切换到该分支
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=self.project_root,
                check=True
            )
        else:
            # 创建并切换到新分支
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.project_root,
                check=True
            )

        return branch_name

    def commit_gate(self, gate_name: str, description: str, files: Optional[List[str]] = None) -> bool:
        """
        提交 Gate 完成

        Args:
            gate_name: Gate 名称 (如 "Gate 1.1")
            description: 描述
            files: 要提交的文件列表，None 表示所有修改的文件

        Returns:
            是否成功
        """
        try:
            # 添加文件
            if files:
                for file in files:
                    subprocess.run(
                        ["git", "add", file],
                        cwd=self.project_root,
                        check=True
                    )
            else:
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.project_root,
                    check=True
                )

            # 生成 commit message
            commit_msg = self._generate_commit_message(gate_name, description)

            # 提交
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.project_root,
                check=True
            )

            return True

        except subprocess.CalledProcessError:
            return False

    def _generate_commit_message(self, gate_name: str, description: str) -> str:
        """
        生成规范的 commit message

        Args:
            gate_name: Gate 名称
            description: 描述

        Returns:
            commit message
        """
        # 提取类型
        type_map = {
            'feat': 'feat',
            'fix': 'fix',
            'refactor': 'refactor',
            'test': 'test',
            'docs': 'docs',
            'chore': 'chore'
        }

        commit_type = 'feat'  # 默认

        # 构造 message
        message = f"{commit_type}: {gate_name} - {description}\n\n"
        message += f"完成 {gate_name}\n\n"
        message += "Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

        return message

    def get_current_branch(self) -> str:
        """
        获取当前分支名

        Returns:
            分支名
        """
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout.strip()

    def get_branch_commits(self, base_branch: str = "main") -> List[Dict[str, str]]:
        """
        获取当前分支相对于基础分支的提交

        Args:
            base_branch: 基础分支

        Returns:
            提交列表
        """
        result = subprocess.run(
            ["git", "log", f"{base_branch}..HEAD", "--pretty=format:%H|%s|%an|%ad", "--date=short"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=True
        )

        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                commits.append({
                    'hash': parts[0],
                    'subject': parts[1],
                    'author': parts[2],
                    'date': parts[3]
                })

        return commits

    def generate_pr_description(self, task_path: str) -> str:
        """
        生成 PR 描述

        Args:
            task_path: 任务路径

        Returns:
            PR 描述
        """
        # 读取 plan.md
        plan_file = Path(task_path) / 'plan.md'
        if not plan_file.exists():
            return "（无 plan.md）"

        with open(plan_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取目标
        goal_match = re.search(r'### 1\.1 核心目标\n\n(.*?)(?=\n###|\Z)', content, re.DOTALL)
        goal = goal_match.group(1).strip() if goal_match else "（未找到目标）"

        # 提取 Gates
        gates = re.findall(r'- \[x\] (Gate .*)', content)

        # 构造 PR 描述
        description = f"## 目标\n\n{goal}\n\n"
        description += f"## 完成的 Gates\n\n"
        for gate in gates:
            description += f"- ✅ {gate}\n"

        description += f"\n## 提交记录\n\n"
        commits = self.get_branch_commits()
        for commit in commits:
            description += f"- {commit['subject']} ({commit['date']})\n"

        return description

    def check_uncommitted_changes(self) -> bool:
        """
        检查是否有未提交的更改

        Returns:
            是否有未提交的更改
        """
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=True
        )

        return bool(result.stdout.strip())
