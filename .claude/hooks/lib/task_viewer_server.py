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
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict
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
        elif parsed_path.path == '/api/annotations':
            # 返回标注数据
            query = parse_qs(parsed_path.query)
            filename = query.get('file', [''])[0]
            self.serve_annotations(filename)
        elif parsed_path.path == '/api/code/diff':
            # 返回代码变更列表
            self.serve_code_diff()
        elif parsed_path.path == '/api/code/file':
            # 返回代码文件指定范围
            query = parse_qs(parsed_path.query)
            file_path = query.get('path', [''])[0]
            start = int(query.get('start', ['1'])[0])
            end = int(query.get('end', ['100'])[0])
            self.serve_code_range(file_path, start, end)
        elif parsed_path.path == '/api/code/annotations':
            # 返回代码标注
            query = parse_qs(parsed_path.query)
            file_path = query.get('path', [''])[0]
            self.serve_code_annotations(file_path)
        else:
            # 静态文件
            super().do_GET()

    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/api/annotations':
            # 保存标注
            self.save_annotation()
        elif parsed_path.path == '/api/code/annotations':
            # 保存代码标注
            self.save_code_annotation()
        else:
            self.send_error(404, "Not found")

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

    def serve_annotations(self, filename: str):
        """返回标注数据"""
        if not filename or not self.task_path:
            self.send_error(400, "Invalid request")
            return

        annotations_file = os.path.join(self.task_path, '.annotations', f'{filename}.json')

        if not os.path.exists(annotations_file):
            # 返回空数组
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'[]')
            return

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()

        with open(annotations_file, 'r', encoding='utf-8') as f:
            self.wfile.write(f.read().encode('utf-8'))

    def save_annotation(self):
        """保存标注"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
            filename = data.get('file')
            annotation = data.get('annotation')

            if not filename or not annotation:
                self.send_error(400, "Invalid data")
                return

            # 确保 .annotations 目录存在
            annotations_dir = os.path.join(self.task_path, '.annotations')
            os.makedirs(annotations_dir, exist_ok=True)

            # 读取现有标注
            annotations_file = os.path.join(annotations_dir, f'{filename}.json')
            annotations = []
            if os.path.exists(annotations_file):
                with open(annotations_file, 'r', encoding='utf-8') as f:
                    annotations = json.load(f)

            # 添加新标注
            annotations.append(annotation)

            # 保存
            with open(annotations_file, 'w', encoding='utf-8') as f:
                json.dump(annotations, f, indent=2, ensure_ascii=False)

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

        except Exception as e:
            self.send_error(500, f"Error saving annotation: {str(e)}")

    # ========== 代码视图 API ==========

    def serve_code_diff(self):
        """返回代码变更列表（基于 git diff）"""
        if not self.task_path:
            self.send_error(400, "No task path")
            return

        try:
            # 获取项目根目录
            project_root = Path(self.task_path).parent.parent

            # 获取当前分支相对于 main 的变更文件
            result = subprocess.run(
                ['git', 'diff', '--name-status', 'main...HEAD'],
                capture_output=True, text=True, cwd=project_root
            )

            changed_files = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0]  # A/M/D
                    file_path = parts[1]
                    # 只包含代码文件
                    if self._is_code_file(file_path):
                        # 获取文件总行数
                        full_path = project_root / file_path
                        total_lines = self._count_lines(full_path) if full_path.exists() else 0

                        # 获取变更统计
                        stat_result = subprocess.run(
                            ['git', 'diff', '--numstat', 'main...HEAD', '--', file_path],
                            capture_output=True, text=True, cwd=project_root
                        )
                        added, deleted = 0, 0
                        if stat_result.stdout.strip():
                            stat_parts = stat_result.stdout.strip().split()
                            if len(stat_parts) >= 2:
                                added = int(stat_parts[0]) if stat_parts[0] != '-' else 0
                                deleted = int(stat_parts[1]) if stat_parts[1] != '-' else 0

                        changed_files.append({
                            'path': file_path,
                            'status': status,
                            'totalLines': total_lines,
                            'added': added,
                            'deleted': deleted
                        })

            self.send_json_response({'files': changed_files})

        except Exception as e:
            self.send_error(500, f"Error getting code diff: {str(e)}")

    def serve_code_range(self, file_path: str, start: int, end: int):
        """返回代码文件指定行范围"""
        if not file_path or not self.task_path:
            self.send_error(400, "Invalid request")
            return

        try:
            project_root = Path(self.task_path).parent.parent
            full_path = project_root / file_path

            if not full_path.exists():
                self.send_error(404, "File not found")
                return

            # 读取文件
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()

            total_lines = len(all_lines)

            # 调整范围
            start = max(1, start)
            end = min(total_lines, end)

            # 获取 diff 信息用于标记变更行
            diff_info = self._get_diff_info(file_path, project_root)

            # 构造响应
            lines = []
            for i in range(start - 1, end):
                line_num = i + 1
                line_content = all_lines[i].rstrip('\n\r')
                line_type = diff_info.get(line_num, 'context')

                lines.append({
                    'num': line_num,
                    'content': line_content,
                    'type': line_type  # context, added, removed
                })

            self.send_json_response({
                'file': file_path,
                'lines': lines,
                'totalLines': total_lines,
                'rangeStart': start,
                'rangeEnd': end,
                'language': self._detect_language(file_path)
            })

        except Exception as e:
            self.send_error(500, f"Error reading code file: {str(e)}")

    def serve_code_annotations(self, file_path: str):
        """返回代码标注"""
        if not file_path or not self.task_path:
            self.send_error(400, "Invalid request")
            return

        annotations_file = Path(self.task_path) / '.annotations' / 'code.json'

        if not annotations_file.exists():
            self.send_json_response({})
            return

        try:
            with open(annotations_file, 'r', encoding='utf-8') as f:
                all_annotations = json.load(f)

            file_annotations = all_annotations.get(file_path, {})
            self.send_json_response(file_annotations)

        except Exception as e:
            self.send_json_response({})

    def save_code_annotation(self):
        """保存代码标注"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
            file_path = data.get('path')
            line_num = str(data.get('line'))  # 用字符串作为 key
            annotation = data.get('annotation')

            if not file_path or not line_num or not annotation:
                self.send_error(400, "Invalid data")
                return

            # 确保 .annotations 目录存在
            annotations_dir = Path(self.task_path) / '.annotations'
            annotations_dir.mkdir(parents=True, exist_ok=True)

            annotations_file = annotations_dir / 'code.json'

            # 读取现有标注
            all_annotations = {}
            if annotations_file.exists():
                with open(annotations_file, 'r', encoding='utf-8') as f:
                    all_annotations = json.load(f)

            # 更新标注
            if file_path not in all_annotations:
                all_annotations[file_path] = {}

            # 生成标注 ID
            annotation['id'] = f"RC-CODE-{int(time.time())}"
            annotation['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S')

            all_annotations[file_path][line_num] = annotation

            # 保存
            with open(annotations_file, 'w', encoding='utf-8') as f:
                json.dump(all_annotations, f, indent=2, ensure_ascii=False)

            self.send_json_response({'success': True, 'id': annotation['id']})

        except Exception as e:
            self.send_error(500, f"Error saving code annotation: {str(e)}")

    def _is_code_file(self, file_path: str) -> bool:
        """判断是否为代码文件"""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
            '.kt', '.scala', '.vue', '.svelte', '.sh', '.sql'
        }
        ext = Path(file_path).suffix.lower()
        return ext in code_extensions

    def _count_lines(self, file_path: Path) -> int:
        """统计文件行数"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return sum(1 for _ in f)
        except:
            return 0

    def _detect_language(self, file_path: str) -> str:
        """检测代码语言"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.vue': 'vue',
            '.sh': 'bash',
            '.sql': 'sql'
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, 'plaintext')

    def _get_diff_info(self, file_path: str, project_root: Path) -> Dict[int, str]:
        """获取文件的 diff 信息，返回行号到变更类型的映射"""
        result = {}

        try:
            diff_result = subprocess.run(
                ['git', 'diff', '-U0', 'main...HEAD', '--', file_path],
                capture_output=True, text=True, cwd=project_root
            )

            diff_text = diff_result.stdout
            if not diff_text:
                return result

            # 解析 diff 输出
            current_line = 0
            for line in diff_text.split('\n'):
                # 匹配 @@ -old_start,old_count +new_start,new_count @@
                match = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    start = int(match.group(1))
                    count = int(match.group(2) or 1)
                    for i in range(count):
                        result[start + i] = 'added'

                elif line.startswith('-') and not line.startswith('---'):
                    pass  # 删除的行在新文件中不存在

        except Exception as e:
            pass

        return result

    def send_json_response(self, data: dict):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

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
