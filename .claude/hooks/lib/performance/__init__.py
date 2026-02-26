"""
性能优化模块

提供增量检查、结果缓存、并行执行和按需加载功能
"""

from .cache import ResultCache, CacheEntry
from .incremental import IncrementalChecker
from .parallel import ParallelExecutor
from .lazy_loader import LazyRuleSetLoader

__all__ = [
    'ResultCache',
    'CacheEntry',
    'IncrementalChecker',
    'ParallelExecutor',
    'LazyRuleSetLoader',
]
