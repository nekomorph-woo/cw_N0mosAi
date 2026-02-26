切换到另一个任务。

## 执行步骤

### 1. 列出所有任务

首先查看可用的任务：

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.task_manager import TaskManager

tm = TaskManager()
tasks = tm.list_tasks()

print("📋 可用任务:")
for task_id, info in tasks.items():
    status_icon = {
        'draft': '📝',
        'in_review': '👀',
        'approved': '✅',
        'executing': '🔵',
        'done': '✅'
    }.get(info.status, '❓')

    print(f"  {status_icon} {task_id}: {info.full_id} [{info.status}]")
```

### 2. 切换任务

使用任务 ID 切换：

```python
task_id = "t1"  # 用户指定的任务 ID

success = tm.set_current_task(task_id)

if success:
    current = tm.get_current_task()
    print(f"✅ 已切换到任务: {current.full_id}")
    print(f"📁 路径: {current.path}")
else:
    print(f"❌ 任务不存在: {task_id}")
```

### 3. 切换 Git 分支（如果有）

如果任务有对应的 Git 分支，自动切换：

```python
from lib.git_manager import GitManager

git_mgr = GitManager()

# 尝试切换到任务分支
# 分支名格式: feat/YYYY-MM-DD-task-name
# 从 full_id 提取: t1-2026-02-26-task-name -> task-name
task_name = '-'.join(current.full_id.split('-')[3:])
date_str = '-'.join(current.full_id.split('-')[1:3])

branch_name = f"feat/{date_str}-{task_name}"

try:
    subprocess.run(
        ["git", "checkout", branch_name],
        check=True,
        capture_output=True
    )
    print(f"✅ 已切换到分支: {branch_name}")
except:
    print(f"⚠️  未找到对应分支: {branch_name}")
```

### 4. 显示任务信息

显示任务的当前状态：

```python
import os

task_path = current.path

# 检查文件存在性
files = {
    'research.md': os.path.exists(f"{task_path}/research.md"),
    'plan.md': os.path.exists(f"{task_path}/plan.md"),
    'code_review.md': os.path.exists(f"{task_path}/code_review.md"),
    'progress.md': os.path.exists(f"{task_path}/progress.md")
}

print("\n📄 任务文件:")
for filename, exists in files.items():
    icon = "✅" if exists else "❌"
    print(f"  {icon} {filename}")
```

## 使用示例

```
用户: /nomos:switch-task t2

Agent 执行:
1. 列出所有任务
2. 切换到 t2
3. 切换 Git 分支（如果有）
4. 显示任务信息
```
