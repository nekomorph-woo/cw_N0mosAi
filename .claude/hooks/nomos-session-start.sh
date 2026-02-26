#!/bin/bash
# SessionStart Hook: 显示当前任务提示

# 读取当前任务
if [ -f ".claude/current-task.txt" ]; then
  CURRENT_TASK=$(cat .claude/current-task.txt)
  if [ -n "$CURRENT_TASK" ]; then
    TASK_ID=$(basename "$CURRENT_TASK" | cut -d'-' -f1)
    echo "📍 当前任务: $TASK_ID ($CURRENT_TASK)"
    echo "使用 /nomos:list-tasks 查看所有任务"
  else
    echo "📋 没有活跃任务。使用 /nomos:start <任务名> 开始新任务"
  fi
else
  echo "📋 没有活跃任务。使用 /nomos:start <任务名> 开始新任务"
fi
