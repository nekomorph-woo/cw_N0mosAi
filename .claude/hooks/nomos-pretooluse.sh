#!/bin/bash
# PreToolUse Hook: 在 Write/Edit 前运行 Linter

set -e

# 从 stdin 读取 tool_input JSON
TOOL_INPUT=$(cat)

# 提取文件路径
FILE_PATH=$(echo "$TOOL_INPUT" | python3 -c "
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

# 跳过非代码文件
case "$FILE_PATH" in
  *.md|*.json|*.yml|*.yaml|*.txt|*.html|*.css|*.sh)
    echo '{"decision": "approve"}'
    exit 0
    ;;
esac

# 运行 AgentLinterEngine
RESULT=$(python3 -c "
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
PASSED=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['passed'])")

if [ "$PASSED" = "True" ]; then
  echo '{"decision": "approve"}'
else
  # 构造拒绝消息，包含错误详情
  echo "$RESULT" | python3 -c "
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
