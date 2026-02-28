#!/bin/bash
# PreToolUse Hook: 在 Write/Edit 前运行 Linter 和阶段检查
# 已集成 Layer 3 动态规则加载

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
    export VIRTUAL_ENV="$VENV_PATH"
    PYTHON_BIN="$VENV_PATH/bin/python3"
else
    PYTHON_BIN="python3"
fi

# 从 .env 文件加载关键环境变量 (ANTHROPIC_*, NOMOS_*)
if [ -f "$PROJECT_ROOT/.env" ]; then
    while IFS='=' read -r key value; do
        case "$key" in
            ANTHROPIC_*|NOMOS_*) export "$key=$value" ;;
        esac
    done < <(grep -E '^(ANTHROPIC_|NOMOS_)' "$PROJECT_ROOT/.env" 2>/dev/null)
fi

# ============================================================
# 主逻辑
# ============================================================

# 从 stdin 读取 tool_input JSON 并保存到临时文件
# (避免 bash echo 解释转义字符)
TOOL_INPUT_FILE=$(mktemp)
cat > "$TOOL_INPUT_FILE"

# 提取文件路径
FILE_PATH=$($PYTHON_BIN -c "
import sys, json
try:
    with open('$TOOL_INPUT_FILE', 'r') as f:
        data = json.load(f)
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

# 运行 AgentLinterEngine (集成动态规则加载)
# 方案 B: Edit 工具合并原文件内容后检查
# 使用临时文件传递 tool_input 避免 bash 转义问题
RESULT=$($PYTHON_BIN -c "
import sys, json, os
sys.path.insert(0, '.claude/hooks')

def get_full_content_for_edit(file_path, old_string, new_string):
    '''
    获取 Edit 操作后的完整文件内容

    策略:
    1. 文件不存在 → 返回 new_string (新文件场景)
    2. old_string 在文件中 → 替换后返回完整内容
    3. old_string 不在文件中 → 返回 new_string (降级处理)
    '''
    # 文件不存在，这是新文件
    if not os.path.exists(file_path):
        return new_string

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()

        # 检查 old_string 是否在文件中
        if old_string and old_string in original:
            # 执行替换，返回完整内容
            return original.replace(old_string, new_string, 1)
        else:
            # old_string 不存在，降级为只检查 new_string
            # 这种情况可能是 replace_all=True 或其他边界情况
            return new_string
    except Exception:
        # 读取失败，降级为只检查 new_string
        return new_string

try:
    from lib.linter_engine import AgentLinterEngine
    from lib.rules.layer1_syntax import RuffRule, ESLintRule, TreeSitterRule
    from lib.rules.layer2_security import BanditRule
    # l3_foundation: 动态规则系统
    from lib.l3_foundation import load_rules_from_task, RuleContext

    engine = AgentLinterEngine()

    # Layer 1: 语法规则
    # Tier 1: 原生工具 (Python -> Ruff, JS/TS -> ESLint)
    engine.register_rule(RuffRule())
    engine.register_rule(ESLintRule())
    # Tier 2: Tree-sitter (其他语言)
    engine.register_rule(TreeSitterRule())

    # Layer 2: 安全规则
    engine.register_rule(BanditRule())

    # Layer 3: 动态业务规则 (从 task/rules/ 加载)
    # 不再有硬编码的预制规则，所有规则由用户在 plan.md 中定义
    context = RuleContext()
    if context.task_dir:
        try:
            dynamic_rules = load_rules_from_task(context.task_dir, strict_mode=False)
            for rule in dynamic_rules:
                # 检查规则是否适用于当前文件
                if rule.should_check('$FILE_PATH'):
                    engine.register_rule(rule)
            if dynamic_rules:
                print(f'[动态规则] 已加载 {len(dynamic_rules)} 个规则', file=sys.stderr)
        except Exception as e:
            # 动态规则加载失败不影响其他规则
            print(f'[动态规则加载警告] {str(e)}', file=sys.stderr)

    # 从临时文件读取 tool_input (避免 bash 转义问题)
    with open('$TOOL_INPUT_FILE', 'r') as f:
        tool_input = json.load(f)
    file_path = tool_input.get('file_path', tool_input.get('path', ''))

    # 判断工具类型，获取完整内容
    if 'content' in tool_input:
        # Write 工具: 直接使用 content
        full_content = tool_input['content']
    elif 'new_string' in tool_input:
        # Edit 工具: 合并原文件内容
        old_string = tool_input.get('old_string', '')
        new_string = tool_input['new_string']
        full_content = get_full_content_for_edit(file_path, old_string, new_string)
    else:
        # 未知工具类型，跳过检查
        full_content = ''

    if full_content:
        result = engine.run(file_path, full_content)
        print(json.dumps(result.to_json()))
    else:
        # 无内容，直接通过
        print(json.dumps({'passed': True, 'file_path': file_path, 'violations': [], 'summary': '无内容，跳过检查'}))
except Exception as e:
    # 如果 Linter 执行失败，记录错误但不阻塞
    import traceback
    print(json.dumps({
        'passed': True,
        'file_path': '$FILE_PATH',
        'violations': [],
        'summary': f'Linter 执行失败: {str(e)}'
    }))
")

# 检查结果
PASSED=$(echo "$RESULT" | $PYTHON_BIN -c "import sys,json; print(str(json.load(sys.stdin)['passed']).lower())")

if [ "$PASSED" = "true" ]; then
  echo '{"decision": "approve"}'
else
  # 构造拒绝消息，包含错误详情
  echo "$RESULT" | $PYTHON_BIN -c "
import sys, json
result = json.load(sys.stdin)
violations = result['violations']
msg = 'Linter 检查未通过:\n'
for v in violations:
    source_prefix = f\"[{v.get('source', 'unknown')}] \" if v.get('source') else ''
    msg += f\"  - [{v['severity']}] {source_prefix}{v['rule']}: {v['message']} (line {v['line']})\n\"
    if v.get('suggestion'):
        msg += f\"    建议: {v['suggestion']}\n\"
output = {'decision': 'reject', 'message': msg}
print(json.dumps(output))
"
fi

# 清理临时文件
rm -f "$TOOL_INPUT_FILE"
