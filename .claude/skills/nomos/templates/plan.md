---
task_id: {TASK_ID}
created: {CREATED}
status: {STATUS}
related_research: ""
current_phase: ""
---

# Plan - {FULL_ID}

## 1. 目标

### 1.1 核心目标

（从 research.md 提炼的核心目标）

### 1.2 成功标准

（可验证的成功标准）

## 2. 架构设计

### 2.1 整体架构

（架构图或描述）

### 2.2 模块划分

（模块划分和职责）

### 2.3 接口设计

（关键接口设计）

## 3. 业务规则

本项目的业务规则约束，将自动生成对应的 Linter 检查规则。

💡 **提示**: 可以参考 `.claude/hooks/lib/rule_examples/` 中的示例规则。

### 3.1 规则列表

#### 规则 1: [规则名称]

- **描述**: [规则描述]
- **参考示例**: [可选] 如: `module_isolation.py.example`
- **Handler**: [command / prompt]
  - `command`: 静态检查 (AST/正则)
  - `prompt`: 语义检查 (AI 判断)
- **严重程度**: [error / warning / info]
- **目标文件**: [文件匹配模式，支持 glob 语法]
  - `*.py`: 所有 .py 文件
  - `src/**/*.py`: src/ 下递归所有 .py 文件
  - `src/api/**/*.py`: src/api/ 下递归所有 .py 文件
  - `*.ts,*.tsx`: 多个模式 (逗号分隔)
  - 如不指定，则检查所有文件
- **详细说明**:
  （详细描述规则要求和检查逻辑）

#### 规则 2: [规则名称]

- **描述**: [规则描述]
- **参考示例**: [可选]
- **Handler**: [command / prompt]
- **严重程度**: [error / warning / info]
- **目标文件**: [文件匹配模式]
- **详细说明**:
  （详细描述规则要求和检查逻辑）

### 3.2 可用示例

`.claude/hooks/lib/rule_examples/` 目录包含以下示例：

| 示例文件 | Handler 类型 | 说明 |
|---------|-------------|------|
| `module_isolation.py.example` | Command | 模块隔离检查 |
| `logger_standard.py.example` | Prompt | Logger 规范检查 |
| `i18n_check.py.example` | Prompt | 国际化检查 |
| `interface_protection.py.example` | Command | 接口保护检查 |

### 3.3 规则元信息

```yaml
# 以下元信息将自动添加到生成的规则脚本
rules_version: "1.0"
auto_generated: true
```

## 4. Phase Gates

### Phase 1: 基础设施

- [ ] Gate 1.1: （描述）
- [ ] Gate 1.2: （描述）

### Phase 2: 核心功能

- [ ] Gate 2.1: （描述）
- [ ] Gate 2.2: （描述）

### Phase 3: 完善与测试

- [ ] Gate 3.1: （描述）
- [ ] Gate 3.2: （描述）

## 5. 实施步骤

### 5.1 Phase 1 详细步骤

（详细步骤）

### 5.2 Phase 2 详细步骤

（详细步骤）

### 5.3 Phase 3 详细步骤

（详细步骤）

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| （风险描述） | （影响） | （缓解措施） |

## 7. Review Comments

### RC-1: （标题）

> 位置: （行号或章节）
> 创建时间: （时间戳）
> 严重程度: [CRITICAL/MAJOR/MINOR/SUGGEST]
> 状态: [pending/pending_ai_question/addressed]

（批注内容）

#### 回复

（Agent 的回复，如有）

---

### RC-2: （标题）

> 位置: （行号或章节）
> 创建时间: （时间戳）
> 严重程度: [MAJOR]
> 状态: [pending]

（批注内容）

---

*最后更新: {CREATED}*
