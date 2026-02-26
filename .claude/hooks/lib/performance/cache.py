"""
结果缓存 (Result Cache)

基于文件 SHA256 hash 的 Lint 结果缓存，提升重复检查性能
"""

import hashlib
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class CacheEntry:
    """缓存条目"""
    file_hash: str
    results: List[Dict[str, Any]]  # list[LintResult] 序列化后的字典
    timestamp: float


class ResultCache:
    """基于文件 hash 的 Lint 结果缓存"""

    def __init__(self, cache_dir: Path):
        """初始化缓存

        Args:
            cache_dir: 缓存目录路径
        """
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, CacheEntry] = {}
        self._load_cache()

    def get(self, file_path: Path) -> Optional[List[Dict[str, Any]]]:
        """查询缓存

        Args:
            file_path: 文件路径

        Returns:
            如果 hash 匹配则返回缓存结果，否则返回 None
        """
        if not file_path.exists():
            return None

        file_hash = self._compute_hash(file_path)
        cache_key = str(file_path)

        entry = self._cache.get(cache_key)
        if entry and entry.file_hash == file_hash:
            return entry.results

        return None

    def put(self, file_path: Path, results: List[Dict[str, Any]]) -> None:
        """写入缓存

        Args:
            file_path: 文件路径
            results: Lint 结果列表
        """
        if not file_path.exists():
            return

        file_hash = self._compute_hash(file_path)
        cache_key = str(file_path)

        entry = CacheEntry(
            file_hash=file_hash,
            results=results,
            timestamp=time.time()
        )

        self._cache[cache_key] = entry
        self._save_cache()

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._save_cache()

    def prune(self, max_age_days: int = 7) -> int:
        """清理过期缓存

        Args:
            max_age_days: 最大保留天数

        Returns:
            清理的条目数量
        """
        now = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        pruned = 0

        keys_to_remove = []
        for key, entry in self._cache.items():
            if now - entry.timestamp > max_age_seconds:
                keys_to_remove.append(key)
                pruned += 1

        for key in keys_to_remove:
            del self._cache[key]

        if pruned > 0:
            self._save_cache()

        return pruned

    def _compute_hash(self, file_path: Path) -> str:
        """计算文件 SHA256

        Args:
            file_path: 文件路径

        Returns:
            SHA256 哈希值
        """
        try:
            return hashlib.sha256(file_path.read_bytes()).hexdigest()
        except (OSError, IOError):
            return ""

    def _load_cache(self) -> None:
        """从磁盘加载缓存"""
        cache_file = self._cache_dir / "lint_cache.json"
        if not cache_file.exists():
            return

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for key, entry_data in data.items():
                self._cache[key] = CacheEntry(**entry_data)

        except (json.JSONDecodeError, OSError, TypeError):
            # 缓存文件损坏，忽略
            pass

    def _save_cache(self) -> None:
        """保存缓存到磁盘"""
        cache_file = self._cache_dir / "lint_cache.json"

        try:
            data = {
                key: asdict(entry)
                for key, entry in self._cache.items()
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        except (OSError, TypeError):
            # 保存失败，忽略
            pass
