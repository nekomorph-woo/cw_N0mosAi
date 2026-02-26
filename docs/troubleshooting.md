# N0mosAi 故障排查

## 常见问题

### Q1: Hooks 未生效

**症状**: 代码写入时没有触发 Linter 检查

**原因**: Hooks 未激活（延迟激活策略）

**解决方案**:
1. 检查 `.claude/settings.json` 中的 hooks 配置
2. 确认 Hook 脚本有执行权限: `chmod +x .claude/hooks/*.sh`

### Q2: Linter 工具未找到

**症状**: 错误信息 "ruff: command not found"

**原因**: Linter 工具未安装

**解决方案**:
```bash
# 安装 Python Linter
pip install ruff bandit

# 安装 JavaScript Linter
npm install -g eslint
```

### Q3: 缓存占用空间过大

**症状**: `.claude/cache/` 目录占用大量磁盘空间

**解决方案**:
```bash
# 清理过期缓存
python -c "from pathlib import Path; from .claude.hooks.lib.performance import ResultCache; ResultCache(Path('.claude/cache')).prune(max_age_days=7)"

# 或手动删除
rm -rf .claude/cache/*
```

### Q4: Task Viewer 无法启动

**症状**: `/nomos:view-task` 命令失败

**原因**: 端口被占用或文件权限问题

**解决方案**:
1. 检查端口 8765 是否被占用
2. 尝试使用其他端口
3. 检查 `.task-viewer.html` 文件权限

### Q5: Git 分支创建失败

**症状**: 创建任务时 Git 分支创建失败

**原因**: Git 配置问题或权限不足

**解决方案**:
1. 确认当前目录是 Git 仓库
2. 检查 Git 用户配置
3. 确认有创建分支的权限

## 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| E001 | Linter 工具未找到 | 安装对应的 Linter 工具 |
| E002 | 配置文件格式错误 | 检查 YAML 语法 |
| E003 | 文件权限不足 | 修改文件权限 |
| E004 | Git 操作失败 | 检查 Git 配置 |

## 调试模式

启用调试日志:
```bash
export NOMOS_DEBUG=1
```

## 获取帮助

- GitHub Issues: https://github.com/anthropics/claude-code/issues
- 文档: 查看 `doc-arch/` 目录
