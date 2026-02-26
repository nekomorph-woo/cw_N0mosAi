查看任务详情并启动 Task Viewer。

## 执行步骤

### 1. 获取任务信息

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.task_manager import TaskManager

tm = TaskManager()

# 如果指定了 task_id，查看该任务；否则查看当前任务
task_id = "t1"  # 或从参数获取

if task_id:
    # 从映射获取任务信息
    tasks = tm.list_tasks()
    if task_id not in tasks:
        print(f"❌ 任务不存在: {task_id}")
        exit(1)
    task_info = tasks[task_id]
else:
    # 获取当前任务
    task_info = tm.get_current_task()
    if not task_info:
        print("❌ 没有当前任务")
        exit(1)

print(f"📋 任务: {task_info.full_id}")
print(f"📁 路径: {task_info.path}")
print(f"📊 状态: {task_info.status}")
print(f"📅 创建: {task_info.created}")
```

### 2. 显示文件状态

```python
import os

task_path = task_info.path

files = ['research.md', 'plan.md', 'code_review.md', 'progress.md']

print("\n📄 文件状态:")
for filename in files:
    filepath = os.path.join(task_path, filename)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        mtime = os.path.getmtime(filepath)
        from datetime import datetime
        mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        print(f"  ✅ {filename} ({size} bytes, 修改于 {mtime_str})")
    else:
        print(f"  ❌ {filename} (不存在)")
```

### 3. 启动 Task Viewer

```python
from lib.task_viewer_server import TaskViewerServer
import threading

# 创建服务器
server = TaskViewerServer(task_path)

# 在后台启动
server.start(auto_shutdown_minutes=30)

print(f"\n🌐 Task Viewer 已启动")
print(f"📍 URL: http://localhost:{server.port}")
print(f"⏱️  将在 30 分钟后自动关闭")
print(f"\n💡 在浏览器中打开上述 URL 查看任务文档")
```

### 4. 显示 Git 信息（如果有）

```python
from lib.git_manager import GitManager

git_mgr = GitManager()

try:
    current_branch = git_mgr.get_current_branch()
    print(f"\n🔀 Git 分支: {current_branch}")

    # 检查是否有未提交的更改
    has_changes = git_mgr.check_uncommitted_changes()
    if has_changes:
        print("⚠️  有未提交的更改")
    else:
        print("✅ 工作区干净")

except:
    print("\n⚠️  不是 Git 仓库")
```

## 使用示例

```
用户: /nomos:view-task t1

Agent 执行:
1. 显示任务信息
2. 显示文件状态
3. 启动 Task Viewer
4. 显示 Git 信息
```

## 注意事项

- Task Viewer 会在后台运行
- 默认 30 分钟后自动关闭
- 可以通过浏览器访问查看文档
- 支持 Markdown 渲染和 Mermaid 图表
