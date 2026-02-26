"""
配置增强模块

提供豁免机制、配置验证等功能
"""

from .exemption import ExemptionEngine, Exemption

__all__ = [
    'ExemptionEngine',
    'Exemption',
]
