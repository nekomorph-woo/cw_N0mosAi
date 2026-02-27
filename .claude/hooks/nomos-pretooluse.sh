#!/bin/bash
# PreToolUse Hook: 在 Write/Edit 前运行 Linter 和阶段检查

set -e

# ============================================================
# 虚拟环境检测与激活
# ============================================================
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$HOOK_DIR")")"
VENV_PATH="$PROJECT_ROOT/.venv"

# 如果虚拟环境存在，设置 PATH 优先使用虚拟环境中的 Python
if [ -d "$VENV_PATH/bin" ]; then
    export PATH="$VENV_PATH/bin:$PATH"
    PYTHON_BIN="$VENV_PATH/bin/python3"
else
    PYTHON_BIN="python3"
fi

# ============================================================
# 主逻辑
# ============================================================

# 从 stdin 读取 tool_input JSON
TOOL_INPUT=$(cat)

# 提取文件路径
FILE_PATH=$(echo "$TOOL_INPUT" | $PYTHON_BIN -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('file_path', data.get('path', '')))
except:
    print('')
")

# 如果无法提取文件路径，直接通过
if [ -z "$FILE_PATH" ]; then
    echo '{"decision": "approve"}'
    exit 0
fi

# ============================================================
# 阶段门控检查
# ============================================================

# 读取当前任务
CURRENT_TASK=""
if [ -f "$PROJECT_ROOT/.claude/current-task.txt" ]; then
    CURRENT_TASK=$(cat "$PROJECT_ROOT/.claude/current-task.txt")
fi

# 如果有当前任务，检查阶段状态
if [ -n "$CURRENT_TASK" ]; then
    PHASE_CHECK=$($PYTHON_BIN -c "
import sys, json, os
sys.path.insert(0, '$PROJECT_ROOT/.claude/hooks')

try:
    from lib.phase_manager import check_phase_for_file

    task_path = '$CURRENT_TASK'
    if not task_path.startswith('/'):
        task_path = os.path.join('$PROJECT_ROOT', task_path)

    allowed, reason = check_phase_for_file(task_path, '$FILE_PATH', '$PROJECT_ROOT')

    print(json.dumps({
        'allowed': allowed,
        'reason': reason
    }))
except Exception as e:
    # 出错时允许通过（向后兼容）
    print(json.dumps({
        'allowed': True,
        'reason': f'阶段检查出错: {str(e)}'
    }))
")

    PHASE_ALLOWED=$(echo "$PHASE_CHECK" | $PYTHON_BIN -c "import sys,json; print(json.load(sys.stdin)['allowed'])")
    PHASE_REASON=$(echo "$PHASE_CHECK" | $PYTHON_BIN -c "import sys,json; print(json.load(sys.stdin)['reason'])")

    if [ "$PHASE_ALLOWED" = "False" ]; then
        echo "{\"decision\": \"reject\", \"message\": \"🚫 阶段门控拦截: $PHASE_REASON\"}"
        exit 0
    fi
fi

# ============================================================
# Linter 检查
# ============================================================

# 跳过非代码文件
case "$FILE_PATH" in
  *.md|*.json|*.yml|*.yaml|*.txt|*.html|*.css|*.sh)
    echo '{"decision": "approve"}'
    exit 0
    ;;
esac

# 运行 AgentLinterEngine
RESULT=$($PYTHON_BIN -c "
import sys, json
sys.path.insert(0, '.claude/hooks')

try:
    from lib.linter_engine import AgentLinterEngine
    from lib.rules.layer1_syntax import RuffRule, ESLintRule
    from lib.rules.layer2_security import BanditRule

    engine = AgentLinterEngine()
    engine.register_rule(RuffRule())
    engine.register_rule(ESLintRule())
    engine.register_rule(BanditRule())

    # 从 stdin 读取内容
    tool_input = json.loads('''$TOOL_INPUT''')
    file_path = tool_input.get('file_path', tool_input.get('path', ''))
    content = tool_input.get('content', tool_input.get('new_string', ''))

    result = engine.run(file_path, content)
    print(json.dumps(result.to_json()))
except Exception as e:
    # 如果 Linter 执行失败，记录错误但不阻塞
    print(json.dumps({
        'passed': True,
        'file_path': '$FILE_PATH',
        'violations': [],
        'summary': f'Linter 执行失败: {str(e)}'
    }))
")

# 检查结果
PASSED=$(echo "$RESULT" | $PYTHON_BIN -c "import sys,json; print(json.load(sys.stdin)['passed'])")

if [ "$PASSED" = "True" ]; then
  echo '{"decision": "approve"}'
else
  # 构造拒绝消息，包含错误详情
  echo "$RESULT" | $PYTHON_BIN -c "
import sys, json
result = json.load(sys.stdin)
violations = result['violations']
msg = 'Linter 检查未通过:\n'
for v in violations:
    msg += f\"  - [{v['severity']}] {v['rule']}: {v['message']} (line {v['line']})\n\"
    if v.get('suggestion'):
        msg += f\"    建议: {v['suggestion']}\n\"
output = {'decision': 'reject', 'message': msg}
print(json.dumps(output))
"
fi
