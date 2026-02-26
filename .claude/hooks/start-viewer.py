#!/usr/bin/env python3
"""
Task Viewer 启动脚本
快速启动任务查看器
"""

import sys
import os

# 添加 lib 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from task_viewer_server import TaskViewerServer, main

if __name__ == '__main__':
    main()
