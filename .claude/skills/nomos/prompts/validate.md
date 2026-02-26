运行 Validator Subagent 审查任务文档。

## 执行步骤

### 1. 获取当前任务

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.task_manager import TaskManager

tm = TaskManager()
current_task = tm.get_current_task()

if not current_task:
    print("❌ 没有当前任务")
    exit(1)

print(f"📋 验证任务: {current_task.full_id}")
```

### 2. 运行 Validator

```python
from lib.validator_subagent import ValidatorSubagent

validator = ValidatorSubagent(current_task.path)
results = validator.run_validation()
```

### 3. 显示验证结果

```python
def display_issues(issues, title):
    if not issues:
        print(f"✅ {title}: 无问题")
        return

    print(f"\n⚠️  {title}: 发现 {len(issues)} 个问题\n")

    # 按严重程度分组
    critical = [i for i in issues if i.severity == 'CRITICAL']
    major = [i for i in issues if i.severity == 'MAJOR']
    minor = [i for i in issues if i.severity == 'MINOR']

    for severity, items in [('CRITICAL', critical), ('MAJOR', major), ('MINOR', minor)]:
        if items:
            print(f"  {severity}:")
            for issue in items:
                print(f"    🔴 [{issue.category}] {issue.message}")
                print(f"       位置: {issue.location}")
                print(f"       建议: {issue.suggestion}")
                print()

# 显示结果
display_issues(results['research'], 'Research.md 验证')
display_issues(results['plan'], 'Plan.md 验证')
```

### 4. 生成审查 Checklist

```python
checklist = validator.generate_checklist()

print("\n📋 审查 Checklist:\n")
for category, items in checklist.items():
    print(f"  {category}:")
    for item in items:
        print(f"    - [ ] {item}")
    print()
```

### 5. 统计摘要

```python
all_issues = results['research'] + results['plan']
critical_count = sum(1 for i in all_issues if i.severity == 'CRITICAL')
major_count = sum(1 for i in all_issues if i.severity == 'MAJOR')
minor_count = sum(1 for i in all_issues if i.severity == 'MINOR')

print(f"\n📊 验证摘要:")
print(f"  - CRITICAL: {critical_count}")
print(f"  - MAJOR: {major_count}")
print(f"  - MINOR: {minor_count}")
print(f"  - 总计: {len(all_issues)}")

if critical_count > 0:
    print(f"\n🚨 有 {critical_count} 个 CRITICAL 问题，必须修复后才能继续")
elif major_count > 0:
    print(f"\n⚠️  有 {major_count} 个 MAJOR 问题，建议修复")
else:
    print(f"\n✅ 验证通过，可以继续")
```

## 验证规则

### Research.md
- 必需章节: 需求理解、代码调研、Protected Interfaces、Why Questions
- Why Questions 必须充分回答（每个问题至少 2-3 句话）
- Protected Interfaces 必须明确列出
- 必须有 YAML Frontmatter

### Plan.md
- 必需章节: 目标、架构设计、Phase Gates、实施步骤
- 至少定义 3 个 Phase Gates
- 所有 CRITICAL/MAJOR Review Comments 必须 addressed
- 目标必须明确可验证

### Protected Interfaces
- 检查代码是否修改了 Protected Interfaces
- 如果修改，必须在 research.md 中说明原因

## 使用场景

- Research 阶段完成后，进入 Plan 阶段前
- Plan 阶段完成后，进入 Execute 阶段前
- 任何时候想检查文档质量

## 注意事项

- Validator 只检查文档结构和完整性，不检查内容正确性
- CRITICAL 问题必须修复
- MAJOR 问题强烈建议修复
- MINOR 问题可选修复
