创建 Pull Request。

## 执行步骤

### 1. 检查当前状态

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.git_manager import GitManager

git_mgr = GitManager()

# 检查是否有未提交的更改
if git_mgr.check_uncommitted_changes():
    print("⚠️  有未提交的更改，请先提交")
    exit(1)

# 获取当前分支
current_branch = git_mgr.get_current_branch()
print(f"📍 当前分支: {current_branch}")
```

### 2. 生成 PR 描述

```python
from lib.task_manager import TaskManager

tm = TaskManager()
current_task = tm.get_current_task()

if not current_task:
    print("❌ 没有当前任务")
    exit(1)

# 生成 PR 描述
pr_description = git_mgr.generate_pr_description(current_task.path)

print("\n📝 PR 描述:\n")
print(pr_description)
```

### 3. 创建 PR

使用 gh CLI 创建 PR：

```bash
gh pr create \
  --title "feat: ${task_name}" \
  --body "${pr_description}" \
  --base main
```

或者显示命令让用户手动执行：

```python
print("\n💡 创建 PR 命令:")
print(f"gh pr create --title 'feat: {current_task.full_id}' --body-file <(echo '{pr_description}') --base main")
```

## PR 描述格式

```markdown
## 目标

（从 plan.md 提取）

## 完成的 Gates

- ✅ Gate 1.1: ...
- ✅ Gate 1.2: ...

## 提交记录

- commit message 1 (date)
- commit message 2 (date)

## 测试

（测试结果）

## 注意事项

（需要注意的事项）
```

## 使用场景

- 任务完成后创建 PR
- 需要代码审查时
- 准备合并到主分支时
