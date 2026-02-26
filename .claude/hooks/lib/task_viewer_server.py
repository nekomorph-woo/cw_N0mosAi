"""
Task Viewer HTTP 服务器
提供任务文档的 Web 查看界面
"""

import http.server
import socketserver
import json
import os
import sys
import signal
import threading
import time
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse


class TaskViewerHandler(http.server.SimpleHTTPRequestHandler):
    """Task Viewer HTTP 请求处理器"""

    def __init__(self, *args, task_path: str = None, **kwargs):
        self.task_path = task_path
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/':
            # 返回主页面
            self.serve_viewer_html()
        elif parsed_path.path == '/api/task':
            # 返回任务数据
            self.serve_task_data()
        elif parsed_path.path == '/api/file':
            # 返回指定文件内容
            query = parse_qs(parsed_path.query)
            filename = query.get('name', [''])[0]
            self.serve_file_content(filename)
        else:
            # 静态文件
            super().do_GET()

    def serve_viewer_html(self):
        """返回 Task Viewer HTML 页面"""
        html_path = Path(__file__).parent.parent.parent / '.task-viewer.html'

        if not html_path.exists():
            self.send_error(404, "Viewer HTML not found")
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        with open(html_path, 'rb') as f:
            self.wfile.write(f.read())

    def serve_task_data(self):
        """返回任务数据（JSON）"""
        if not self.task_path or not os.path.exists(self.task_path):
            self.send_error(404, "Task not found")
            return

        # 读取任务文件夹中的所有 .md 文件
        task_files = {}
        for filename in ['research.md', 'plan.md', 'code_review.md', 'progress.md']:
            filepath = os.path.join(self.task_path, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    task_files[filename] = f.read()

        # 读取 short-id-mapping.json 获取任务信息
        mapping_file = Path(self.task_path).parent.parent / 'short-id-mapping.json'
        task_info = {}
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
                task_id = Path(self.task_path).name.split('-')[0]
                task_info = mapping.get(task_id, {})

        response_data = {
            'task_info': task_info,
            'files': task_files
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

    def serve_file_content(self, filename: str):
        """返回指定文件内容"""
        if not filename or not self.task_path:
            self.send_error(400, "Invalid request")
            return

        filepath = os.path.join(self.task_path, filename)
        if not os.path.exists(filepath):
            self.send_error(404, "File not found")
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

        with open(filepath, 'r', encoding='utf-8') as f:
            self.wfile.write(f.read().encode('utf-8'))

    def log_message(self, format, *args):
        """自定义日志输出"""
        # 只输出错误日志
        if args[1] != '200':
            super().log_message(format, *args)


class TaskViewerServer:
    """Task Viewer 服务器管理器"""

    def __init__(self, task_path: str, port: Optional[int] = None):
        """
        初始化服务器

        Args:
            task_path: 任务文件夹路径
            port: 端口号，None 则自动分配
        """
        self.task_path = task_path
        self.port = port or self._find_available_port()
        self.server = None
        self.server_thread = None
        self.shutdown_timer = None

    def _find_available_port(self, start_port: int = 8000, max_attempts: int = 100) -> int:
        """
        查找可用端口

        Args:
            start_port: 起始端口
            max_attempts: 最大尝试次数

        Returns:
            可用端口号
        """
        for port in range(start_port, start_port + max_attempts):
            try:
                with socketserver.TCPServer(("", port), None) as s:
                    return port
            except OSError:
                continue
        raise RuntimeError(f"无法找到可用端口 (尝试了 {start_port}-{start_port + max_attempts})")

    def start(self, auto_shutdown_minutes: int = 30):
        """
        启动服务器

        Args:
            auto_shutdown_minutes: 自动关闭时间（分钟）
        """
        # 创建服务器
        handler = lambda *args, **kwargs: TaskViewerHandler(
            *args, task_path=self.task_path, **kwargs
        )

        self.server = socketserver.TCPServer(("", self.port), handler)

        # 在后台线程运行服务器
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

        # 设置自动关闭定时器
        if auto_shutdown_minutes > 0:
            self.shutdown_timer = threading.Timer(
                auto_shutdown_minutes * 60,
                self.stop
            )
            self.shutdown_timer.daemon = True
            self.shutdown_timer.start()

        print(f"✅ Task Viewer 已启动")
        print(f"📍 URL: http://localhost:{self.port}")
        print(f"⏱️  将在 {auto_shutdown_minutes} 分钟后自动关闭")

    def stop(self):
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("\n🛑 Task Viewer 已关闭")

        if self.shutdown_timer:
            self.shutdown_timer.cancel()

    def wait(self):
        """等待服务器关闭"""
        if self.server_thread:
            try:
                self.server_thread.join()
            except KeyboardInterrupt:
                print("\n⚠️  收到中断信号")
                self.stop()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python task_viewer_server.py <task_path> [port]")
        sys.exit(1)

    task_path = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not os.path.exists(task_path):
        print(f"❌ 任务路径不存在: {task_path}")
        sys.exit(1)

    # 创建并启动服务器
    server = TaskViewerServer(task_path, port)

    # 注册信号处理
    signal.signal(signal.SIGINT, lambda s, f: server.stop())
    signal.signal(signal.SIGTERM, lambda s, f: server.stop())

    server.start()
    server.wait()


if __name__ == '__main__':
    main()
