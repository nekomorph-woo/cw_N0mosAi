"""
Revert Manager
管理 Git Revert 和失败记录
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


class RevertManager:
    """Revert Manager - 管理代码回滚和失败记录"""

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化 Revert Manager

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or os.getcwd())
        self.revert_log_file = self.project_root / '.claude' / 'revert-log.json'

    def should_revert(self, reason: str) -> bool:
        """
        判断是否应该 revert

        Args:
            reason: 原因

        Returns:
            是否应该 revert
        """
        # Revert 触发条件
        revert_keywords = [
            '严重错误',
            '无法修复',
            '方向错误',
            '架构问题',
            '性能严重下降',
            '破坏性变更',
            '测试全部失败'
        ]

        return any(keyword in reason for keyword in revert_keywords)

    def execute_revert(self, commit_hash: Optional[str] = None, reason: str = "") -> bool:
        """
        执行 Git Revert

        Args:
            commit_hash: 要 revert 的 commit，None 表示最后一个 commit
            reason: Revert 原因

        Returns:
            是否成功
        """
        try:
            if commit_hash:
                # Revert 指定 commit
                result = subprocess.run(
                    ["git", "revert", "--no-edit", commit_hash],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
            else:
                # Revert 最后一个 commit
                result = subprocess.run(
                    ["git", "revert", "--no-edit", "HEAD"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )

            # 记录 revert
            self._log_revert(commit_hash or "HEAD", reason)

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Revert 失败: {e.stderr}")
            return False

    def _log_revert(self, commit_hash: str, reason: str):
        """
        记录 revert 到日志

        Args:
            commit_hash: Commit hash
            reason: 原因
        """
        import json

        # 读取现有日志
        reverts = []
        if self.revert_log_file.exists():
            with open(self.revert_log_file, 'r') as f:
                reverts = json.load(f)

        # 添加新记录
        reverts.append({
            'commit': commit_hash,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'branch': self._get_current_branch()
        })

        # 保存
        self.revert_log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.revert_log_file, 'w') as f:
            json.dump(reverts, f, indent=2, ensure_ascii=False)

    def sync_to_project_why(self, reason: str, lesson: str):
        """
        同步失败教训到 project-why.md

        Args:
            reason: 失败原因
            lesson: 经验教训
        """
        from .why_first_engine import WhyFirstEngine

        why_engine = WhyFirstEngine(str(self.project_root))

        # 添加到经验教训
        title = f"Revert: {reason[:50]}"
        content = f"""
**原因**: {reason}

**教训**: {lesson}

**避免方法**:
- 在实施前充分验证方案
- 及时发现问题并果断回滚
- 记录失败原因避免重复
"""

        why_engine.add_knowledge(
            category='经验教训',
            title=title,
            content=content.strip()
        )

    def get_revert_history(self, limit: int = 10) -> List[Dict]:
        """
        获取 revert 历史

        Args:
            limit: 返回数量

        Returns:
            Revert 记录列表
        """
        import json

        if not self.revert_log_file.exists():
            return []

        with open(self.revert_log_file, 'r') as f:
            reverts = json.load(f)

        return reverts[-limit:]

    def _get_current_branch(self) -> str:
        """获取当前分支"""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def analyze_revert_patterns(self) -> Dict[str, int]:
        """
        分析 revert 模式

        Returns:
            模式统计
        """
        import json

        if not self.revert_log_file.exists():
            return {}

        with open(self.revert_log_file, 'r') as f:
            reverts = json.load(f)

        # 统计原因
        reasons = {}
        for revert in reverts:
            reason = revert.get('reason', 'Unknown')
            # 提取关键词
            for keyword in ['错误', '性能', '架构', '测试', '破坏']:
                if keyword in reason:
                    reasons[keyword] = reasons.get(keyword, 0) + 1

        return reasons

    def suggest_prevention(self) -> List[str]:
        """
        根据历史 revert 建议预防措施

        Returns:
            建议列表
        """
        patterns = self.analyze_revert_patterns()

        suggestions = []

        if patterns.get('测试', 0) > 2:
            suggestions.append('建议: 加强测试覆盖，在 commit 前运行完整测试')

        if patterns.get('架构', 0) > 1:
            suggestions.append('建议: 在 Plan 阶段进行更充分的架构设计评审')

        if patterns.get('性能', 0) > 1:
            suggestions.append('建议: 添加性能基准测试，避免性能回退')

        if patterns.get('错误', 0) > 3:
            suggestions.append('建议: 增加 Linter 规则，在代码写入前捕获更多错误')

        if not suggestions:
            suggestions.append('暂无特定建议，继续保持良好的开发习惯')

        return suggestions
