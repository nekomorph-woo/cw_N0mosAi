归档已完成的任务。

## 执行步骤

### 1. 选择要归档的任务

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.task_manager import TaskManager

tm = TaskManager()
tasks = tm.list_tasks()

# 列出已完成的任务
done_tasks = {tid: info for tid, info in tasks.items() if info.status == 'done'}

print("📋 已完成的任务:\n")
for tid, info in done_tasks.items():
    print(f"  - {tid}: {info.full_id}")
```

### 2. 归档任务

```python
import shutil
import os

task_id = "t1"  # 用户指定

if task_id not in done_tasks:
    print(f"❌ 任务 {task_id} 不存在或未完成")
    exit(1)

task_info = done_tasks[task_id]

# 创建归档目录
archive_dir = "tasks/.archive"
os.makedirs(archive_dir, exist_ok=True)

# 移动任务文件夹
src = task_info.path
dst = os.path.join(archive_dir, os.path.basename(src))

shutil.move(src, dst)

# 更新映射
mapping = tm._load_mapping()
mapping[task_id]['archived'] = True
mapping[task_id]['archived_at'] = datetime.now().isoformat()
mapping[task_id]['path'] = dst
tm._save_mapping(mapping)

print(f"✅ 已归档任务: {task_info.full_id}")
print(f"📁 归档位置: {dst}")
```

### 3. 清理 Git 分支（可选）

```python
from lib.git_manager import GitManager

git_mgr = GitManager()

# 删除对应的 Git 分支
branch_name = f"feat/{task_info.full_id.split('-', 1)[1]}"

try:
    subprocess.run(["git", "branch", "-d", branch_name], check=True)
    print(f"✅ 已删除分支: {branch_name}")
except:
    print(f"⚠️  分支不存在或无法删除: {branch_name}")
```

## 归档规则

- 只能归档状态为 'done' 的任务
- 归档后任务移动到 tasks/.archive/
- 映射文件中标记 archived: true
- 可选删除对应的 Git 分支

## 使用场景

- 任务完成并合并后
- 定期清理已完成任务
- 保持任务列表整洁
