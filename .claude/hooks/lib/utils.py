"""
工具函数
"""

import os
import tempfile
from pathlib import Path
from typing import Optional


def create_temp_file(content: str, suffix: str = ".tmp") -> str:
    """
    创建临时文件并写入内容

    Args:
        content: 文件内容
        suffix: 文件后缀

    Returns:
        临时文件路径
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
    except:
        os.close(fd)
        raise
    return path


def detect_language(file_path: str) -> Optional[str]:
    """
    根据文件扩展名检测语言

    Args:
        file_path: 文件路径

    Returns:
        语言名称 (python/javascript/typescript/go/rust 等) 或 None
    """
    ext = Path(file_path).suffix.lower()

    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "c",
        ".hpp": "cpp",
    }

    return language_map.get(ext)


def is_code_file(file_path: str) -> bool:
    """
    判断是否为代码文件

    Args:
        file_path: 文件路径

    Returns:
        是否为代码文件
    """
    return detect_language(file_path) is not None
