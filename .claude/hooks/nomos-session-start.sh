#!/bin/bash
# SessionStart Hook: 显示当前任务提示 + 注入 N0mosAi 规范

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
# 注入 N0mosAi 输出规范
# ============================================================
NOMOS_STYLE="$PROJECT_ROOT/.claude/rules/nomos-style.md"

if [ -f "$NOMOS_STYLE" ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║                    🤖 N0mosAi 规范已加载                           ║"
    echo "╠════════════════════════════════════════════════════════════════════╣"
    echo "║  输出格式: ASCII 方框图 | Markdown 表格 | Emoji 状态              ║"
    echo "║  流程规范: Why-First → Research → Plan → Execute → Review         ║"
    echo "║  命令: /nomos:start | /nomos:list-tasks | /nomos:validate         ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo ""
fi

# ============================================================
# 显示当前任务状态
# ============================================================
CURRENT_TASK_FILE="$PROJECT_ROOT/.claude/current-task.txt"

if [ -f "$CURRENT_TASK_FILE" ]; then
  CURRENT_TASK=$(cat "$CURRENT_TASK_FILE")
  if [ -n "$CURRENT_TASK" ]; then
    TASK_DIR="$PROJECT_ROOT/$CURRENT_TASK"
    if [ -d "$TASK_DIR" ]; then
      TASK_ID=$(basename "$CURRENT_TASK" | cut -d'-' -f1)
      echo "📍 当前任务: $TASK_ID ($CURRENT_TASK)"
      echo "   使用 /nomos:list-tasks 查看所有任务"
      echo ""
    else
      echo "📋 任务目录不存在，已清理"
      rm -f "$CURRENT_TASK_FILE"
    fi
  else
    echo "📋 没有活跃任务。使用 /nomos:start <任务名> 开始新任务"
    echo ""
  fi
else
  echo "📋 没有活跃任务。使用 /nomos:start <任务名> 开始新任务"
  echo ""
fi
