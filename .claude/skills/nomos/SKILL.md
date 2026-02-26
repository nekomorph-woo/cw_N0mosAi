---
name: nomos
description: Agent 刚性工作流管理
version: 0.1.0
commands:
  - name: start
    description: 启动新任务的刚性工作流
    args: "[task_name]"
  - name: list-tasks
    description: 列出所有任务及状态
    args: "[--status=...] [--recent=N]"
  - name: new-task
    description: 创建新任务并初始化 Git 分支
    args: "<task_name> [type]"
  - name: switch-task
    description: 切换到另一个任务
    args: "<task_id>"
  - name: view-task
    description: 查看任务详情并启动 Task Viewer
    args: "[task_id]"
---

# /nomos

Agent 刚性工作流管理工具。通过 Hooks 物理门控确保代码质量。

## 可用命令

| 命令 | 说明 |
|------|------|
| `/nomos:start <任务名>` | 启动新任务 |
| `/nomos:list-tasks` | 列出所有任务 |

## 核心理念

N0mosAi 通过以下机制确保 Agent 遵循刚性工作流：

1. **Hooks 物理门控**: PreToolUse Hook 在代码写入前强制运行 Linter
2. **Task 文件夹隔离**: 每个任务独立文件夹，避免混乱
3. **Phase Gates**: 阶段门控确保流程完整性
4. **Review Comments**: 人类批注机制确保质量

## 使用流程

```
1. /nomos:start <任务名>  → 创建任务
2. Research 阶段          → 理解需求
3. Plan 阶段              → 设计方案
4. Execute 阶段           → 实现代码
5. Review 阶段            → 审查验收
```
