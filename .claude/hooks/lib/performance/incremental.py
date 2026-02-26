"""
增量检查器 (Incremental Checker)

只检查 git diff 变更的文件，结合缓存提升大型项目检查性能
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Callable
from .cache import ResultCache


class IncrementalChecker:
    """增量 Linter 检查器 — 只检查 git diff 变更的文件"""

    def __init__(self, repo_root: Path, cache: ResultCache):
        """初始化增量检查器

        Args:
            repo_root: Git 仓库根目录
            cache: 结果缓存实例
        """
        self._repo_root = repo_root
        self._cache = cache

    def get_changed_files(self, base_ref: str = "HEAD") -> List[Path]:
        """通过 git diff 获取变更文件列表

        Args:
            base_ref: 基准引用 (默认 HEAD)

        Returns:
            变更文件路径列表
        """
        try:
            # 获取未暂存的变更
            result = subprocess.run(
                ['git', 'diff', '--name-only', base_ref],
                cwd=self._repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                files = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        file_path = self._repo_root / line
                        if file_path.exists() and file_path.is_file():
                            files.append(file_path)
                return files

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return []

    def get_staged_files(self) -> List[Path]:
        """获取已暂存的文件列表

        Returns:
            已暂存文件路径列表
        """
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=self._repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                files = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        file_path = self._repo_root / line
                        if file_path.exists() and file_path.is_file():
                            files.append(file_path)
                return files

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return []

    def check(self, files: List[Path],
              check_fn: Callable[[Path], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """对变更文件执行增量检查

        Args:
            files: 文件列表
            check_fn: 检查函数，接受文件路径，返回 Lint 结果列表

        Returns:
            所有文件的 Lint 结果
        """
        results = []
        uncached = []

        # 先尝试从缓存获取
        for f in files:
            cached = self._cache.get(f)
            if cached is not None:
                results.extend(cached)
            else:
                uncached.append(f)

        # 对未缓存的文件执行检查
        if uncached:
            new_results = self._run_checks(uncached, check_fn)
            results.extend(new_results)

        return results

    def _run_checks(self, files: List[Path],
                    check_fn: Callable[[Path], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """运行检查并更新缓存

        Args:
            files: 文件列表
            check_fn: 检查函数

        Returns:
            Lint 结果列表
        """
        all_results = []

        for file_path in files:
            try:
                file_results = check_fn(file_path)
                all_results.extend(file_results)

                # 更新缓存
                self._cache.put(file_path, file_results)

            except Exception:
                # 检查失败，跳过该文件
                continue

        return all_results
