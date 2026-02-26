创建任务分支并开始工作。

## 执行步骤

### 1. 创建任务

使用 TaskManager 创建任务（如果尚未创建）：

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.task_manager import TaskManager

tm = TaskManager()
task = tm.create_task("任务名", "feat")
```

### 2. 创建 Git 分支

使用 GitManager 创建任务分支：

```python
from lib.git_manager import GitManager

git_mgr = GitManager()
branch_name = git_mgr.create_branch(
    task_id=task.task_id,
    task_name="任务名",
    branch_type="feat"  # 或 fix/refactor/test/docs
)

print(f"✅ 已创建并切换到分支: {branch_name}")
```

### 3. 分支命名规范

分支名格式: `<type>/<date>-<task-name>`

示例:
- `feat/2026-02-26-user-login`
- `fix/2026-02-26-auth-bug`
- `refactor/2026-02-26-api-cleanup`

### 4. 开始工作

现在可以开始 Research → Plan → Execute 流程。

每完成一个 Gate，使用 GitManager 提交：

```python
git_mgr.commit_gate(
    gate_name="Gate 1.1",
    description="完成基础设施搭建",
    files=None  # None 表示提交所有修改
)
```

## 注意事项

- 分支会自动从当前分支（通常是 main）创建
- 如果分支已存在，会切换到该分支
- commit message 会自动生成规范格式
