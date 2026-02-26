#!/bin/bash
# UserPromptSubmit Hook: 智能检测用户意图

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

# 从 stdin 读取用户输入
USER_INPUT=$(cat)

# Why-First 关键词检测
$PYTHON_BIN << EOF
import sys

user_input = """$USER_INPUT"""

# Why-First 关键词
why_keywords = [
    '为什么',
    'why',
    '原因',
    '动机',
    '目的',
    '为什么需要',
    '为什么要',
    '怎么想',
    '思路',
    '设计理由'
]

# 检测是否需要 Why-First
user_lower = user_input.lower()
needs_why_first = any(keyword in user_lower for keyword in why_keywords)

if needs_why_first:
    # 输出提示信息（不阻塞，只是提示）
    import json
    feedback = {
        "decision": "approve",
        "reason": "检测到 Why 问题，建议先完成 Why-First 阶段"
    }
    print(json.dumps(feedback))
else:
    # 不输出任何内容，让流程继续
    print("")
EOF
