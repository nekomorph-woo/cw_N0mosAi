#!/bin/bash
# SessionStart Hook: 显示当前任务提示

# ============================================================
# 虚拟环境检测与激活
# ============================================================
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$HOOK_DIR")")"
VENV_PATH="$PROJECT_ROOT/.venv"

# 如果虚拟环境存在，设置 PATH 优先使用虚拟环境中的 Python
if [ -d "$VENV_PATH/bin" ]; then
    export PATH="$VENV_PATH/bin:$PATH"
fi

# ============================================================
# 主逻辑
# ============================================================

# 读取当前任务
CURRENT_TASK_FILE="$PROJECT_ROOT/.claude/current-task.txt"

if [ -f "$CURRENT_TASK_FILE" ]; then
  CURRENT_TASK=$(cat "$CURRENT_TASK_FILE")
  if [ -n "$CURRENT_TASK" ]; then
    TASK_DIR="$PROJECT_ROOT/$CURRENT_TASK"
    if [ -d "$TASK_DIR" ]; then
      TASK_ID=$(basename "$CURRENT_TASK" | cut -d'-' -f1)
      echo "📍 当前任务: $TASK_ID ($CURRENT_TASK)"
      echo "使用 /nomos:list-tasks 查看所有任务"
    else
      echo "📋 任务目录不存在，已清理"
      rm -f "$CURRENT_TASK_FILE"
    fi
  else
    echo "📋 没有活跃任务。使用 /nomos:start <任务名> 开始新任务"
  fi
else
  echo "📋 没有活跃任务。使用 /nomos:start <任务名> 开始新任务"
fi
