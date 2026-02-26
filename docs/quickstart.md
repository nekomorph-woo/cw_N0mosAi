# N0mosAi 快速开始

## 5 分钟上手教程

### 1. 创建新任务

使用 `/nomos:start` 命令创建新任务:

```
/nomos:start user-authentication
```

这将:
- 创建任务文件夹 `tasks/t1-2026-02-26-user-authentication/`
- 初始化 Git 分支 `feat/2026-02-26-user-authentication`
- 生成任务文档模板

### 2. Why-First 阶段

在 `research.md` 中回答 Why Questions:
- 为什么需要这个功能?
- 为什么选择这个技术方案?
- 为什么现在做?

### 3. Research 阶段

调研代码库，识别 Protected Interfaces。

### 4. Plan 阶段

在 `plan.md` 中定义 Phase Gates 和实施步骤。

### 5. Execute 阶段

实现代码，Linter 自动检查。

### 6. Review 阶段

使用 Task Viewer 查看和处理 Review Comments。

## 最小配置示例

`.claude/settings.json`:
```json
{
  "hooks": {}
}
```

## 常用命令

- `/nomos:list-tasks`: 列出所有任务
- `/nomos:switch-task <task_id>`: 切换任务
- `/nomos:view-task`: 启动 Task Viewer
- `/nomos:validate`: 运行 Validator 审查
- `/nomos:pr`: 生成 Pull Request

## 下一步

- 阅读 [配置参考](config_ref.md) 了解详细配置
- 查看 [故障排查](troubleshooting.md) 解决常见问题
