#!/bin/bash
# Stop Hook: 检查 Phase Gates 和 Review Comments

set -e

# 读取当前任务
CURRENT_TASK=""
if [ -f ".claude/current-task.txt" ]; then
  CURRENT_TASK=$(cat .claude/current-task.txt)
fi

if [ -z "$CURRENT_TASK" ]; then
  echo '{"decision": "approve"}'
  exit 0
fi

# 检查 plan.md 的 Gates 和 Review Comments
python3 -c "
import sys, json, re, os

task_path = '$CURRENT_TASK'
plan_path = os.path.join(task_path, 'plan.md')

if not os.path.exists(plan_path):
    print(json.dumps({'decision': 'approve'}))
    sys.exit(0)

with open(plan_path, 'r') as f:
    content = f.read()

# 检查未完成的 Gates (未勾选的 checkbox)
unchecked_gates = re.findall(r'- \[ \] (Gate .*)', content)

# 检查未处理的 Review Comments (CRITICAL/MAJOR + pending)
pending_reviews = []
rc_blocks = re.findall(r'### RC-\d+:.*?(?=### RC-|\Z)', content, re.DOTALL)
for block in rc_blocks:
    if 'pending' in block and ('CRITICAL' in block or 'MAJOR' in block):
        title = re.search(r'### (RC-\d+:.*)', block)
        if title:
            pending_reviews.append(title.group(1).strip())

if unchecked_gates or pending_reviews:
    msg = ''
    if unchecked_gates:
        msg += '未完成的 Gates:\n'
        for g in unchecked_gates[:5]:
            msg += f'  - [ ] {g}\n'
    if pending_reviews:
        msg += '未处理的 Review Comments:\n'
        for r in pending_reviews[:5]:
            msg += f'  - {r}\n'
    print(json.dumps({'decision': 'reject', 'message': msg}))
else:
    print(json.dumps({'decision': 'approve'}))
"
