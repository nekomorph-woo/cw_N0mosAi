#!/bin/bash
# UserPromptSubmit Hook: 智能检测用户意图

set -e

# 读取用户输入
USER_INPUT=$(cat)

# 检测是否包含 Why-First 关键词
python3 << 'EOF'
import sys
import os

sys.path.insert(0, '.claude/hooks')

user_input = """$USER_INPUT"""

# Why-First 关键词
why_keywords = [
    '为什么',
    'why',
    '原因',
    '动机',
    '目的'
]

# 检测是否需要 Why-First
needs_why_first = any(keyword in user_input.lower() for keyword in why_keywords)

if needs_why_first:
    print("检测到 Why 问题，建议先完成 Why-First 阶段")
else:
    print("")  # 不输出任何内容，让流程继续
EOF
