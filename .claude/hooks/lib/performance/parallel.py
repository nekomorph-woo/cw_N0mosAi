"""
并行执行器 (Parallel Executor)

使用多线程并行执行 Lint 任务，提升多核机器性能
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Dict
from pathlib import Path


class ParallelExecutor:
    """三层规则并行执行器"""

    def __init__(self, max_workers: int = 4):
        """初始化并行执行器

        Args:
            max_workers: 最大工作线程数
        """
        self._max_workers = max_workers

    def execute(self, tasks: List[Callable[[], List[Dict[str, Any]]]]) -> List[Dict[str, Any]]:
        """并行执行多个 Lint 任务

        Args:
            tasks: 任务列表，每个任务是一个无参数的 callable，返回 Lint 结果列表

        Returns:
            所有任务的 Lint 结果
        """
        results = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {pool.submit(task): task for task in tasks}

            for future in as_completed(futures):
                try:
                    task_results = future.result()
                    if task_results:
                        results.extend(task_results)
                except Exception:
                    # 任务执行失败，跳过
                    continue

        return results

    def execute_on_files(self, files: List[Path],
                         check_fn: Callable[[Path], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """并行对多个文件执行检查

        Args:
            files: 文件列表
            check_fn: 检查函数，接受文件路径，返回 Lint 结果列表

        Returns:
            所有文件的 Lint 结果
        """
        results = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {pool.submit(check_fn, f): f for f in files}

            for future in as_completed(futures):
                try:
                    file_results = future.result()
                    if file_results:
                        results.extend(file_results)
                except Exception:
                    # 文件检查失败，跳过
                    continue

        return results
