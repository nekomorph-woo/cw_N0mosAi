# nOmOsAi - 开发计划总览

> **文档版本**: 1.0
> **最后更新**: 2026-02-25
> **状态**: Draft

本文档提供 Nomos 系统的完整开发计划总览，包括阶段划分、优先级排序和依赖关系。

---

## 目录

1. [开发阶段总览](#1-开发阶段总览)
2. [需求优先级矩阵](#2-需求优先级矩阵)
3. [技术栈与依赖](#3-技术栈与依赖)
4. [里程碑与交付物](#4-里程碑与交付物)
5. [风险评估与缓解](#5-风险评估与缓解)
6. [开发文档索引](#6-开发文档索引)

---

## 1. 开发阶段总览

### 1.1 四阶段开发模型

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         开发阶段总览                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 0: MVP (最小可行产品)                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 目标: 验证核心刚性流程可行性                                           │   │
│  │ 内容: Task 文件夹 + 基础 Hooks + 一二层 Linter + 基础 SKILL            │   │
│  │ 依赖: 无                                                              │   │
│  │ 预计工作量: 核心功能                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Phase 1: Core Features (核心功能)                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 目标: 完善刚性流程，支持完整工作流                                     │   │
│  │ 内容: Task Viewer + 标注系统 + Why-First + Git 集成                   │   │
│  │ 依赖: Phase 0 完成                                                    │   │
│  │ 预计工作量: 主要功能                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Phase 2: Advanced Features (高级功能)                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 目标: 提升用户体验和智能化                                             │   │
│  │ 内容: Validator Subagent + Revert Manager + 高级 SKILL                │   │
│  │ 依赖: Phase 1 完成                                                    │   │
│  │ 预计工作量: 增强功能                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  Phase 3: Optional Features (可选功能)                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 目标: 扩展能力和性能优化                                               │   │
│  │ 内容: 多语言支持 + 增量检查 + 性能优化                                 │   │
│  │ 依赖: Phase 2 完成                                                    │   │
│  │ 预计工作量: 可选增强                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 阶段依赖关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         阶段依赖关系图                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 0 (MVP)                                                               │
│  ├── Task 文件夹系统 ──────────────────────────────────────┐                │
│  ├── 基础 Hooks (PreToolUse/Stop) ─────────────────────────┼──┐            │
│  ├── AgentLinterEngine 核心 ───────────────────────────────┤  │            │
│  └── 基础 SKILL (/nomos) ─────────────────────────────┘  │            │
│                              ↓                               ↓            │
│  Phase 1 (Core)                                              │            │
│  ├── Task Viewer HTML ──────────────────────────────────────┤            │
│  ├── 标注系统 ──────────────────────────────────────────────┤            │
│  ├── Why-First 引擎 ────────────────────────────────────────┤            │
│  └── Git 集成 (分支/Commit) ────────────────────────────────┘            │
│                              ↓                                            │
│  Phase 2 (Advanced)                                                       │
│  ├── Validator Subagent ───────────────────────────────────┐            │
│  ├── Revert Manager ────────────────────────────────────────┤            │
│  ├── 诚实追问引擎 ──────────────────────────────────────────┤            │
│  └── project-why.md 智能维护 ───────────────────────────────┘            │
│                              ↓                                            │
│  Phase 3 (Optional)                                                       │
│  ├── Tree-sitter 多语言支持                                                               │
│  ├── 增量 Linter 检查                                                                     │
│  ├── 第三层规则 YAML 配置                                                                 │
│  └── 性能优化 (缓存/并行)                                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 需求优先级矩阵

### 2.1 Must Have (P0) - 38 项

| 模块 | 需求 ID | 需求描述 | 开发阶段 |
|------|---------|----------|----------|
| **Linter** | FR-001 | BaseRule 标准接口 | Phase 0 |
| **Linter** | FR-002 | AgentLinterEngine 核心引擎 | Phase 0 |
| **Linter** | FR-007 | 第一层规则(语法/风格) | Phase 0 |
| **Linter** | FR-008 | 第二层规则(安全) | Phase 0 |
| **Linter** | FR-009 | JSON 格式 Linter 报告 | Phase 0 |
| **Hooks** | FR-003 | PreToolUse Hook 强制 Linter | Phase 0 |
| **Hooks** | FR-006 | Stop Hook 阶段门控 | Phase 0 |
| **Hooks** | FR-017 | SessionStart Hook 轻量级提示 | Phase 0 |
| **Hooks** | FR-018 | UserPromptSubmit Hook 智能检测 | Phase 1 |
| **Task** | FR-004 | Task 文件夹隔离 | Phase 0 |
| **Task** | FR-016 | current-task.txt 状态文件 | Phase 0 |
| **Task** | FR-019 | /nomos:switch-task | Phase 1 |
| **Task** | FR-020 | /nomos:list-tasks | Phase 1 |
| **标注** | FR-005 | 标注循环 | Phase 1 |
| **标注** | FR-021 | 诚实追问机制 | Phase 2 |
| **标注** | FR-029 | 标注格式与 Review Comments 一致 | Phase 1 |
| **标注** | FR-030 | 右键创建/左键查看标注 | Phase 1 |
| **标注** | FR-031 | 标注历史持久化 | Phase 1 |
| **标注** | FR-032 | pending_ai_question 状态 | Phase 1 |
| **标注** | FR-033 | Markdown 特殊格式标注 | Phase 1 |
| **标注** | FR-034 | 渲染/源码视图切换 | Phase 1 |
| **标注** | FR-035 | 内容动态刷新 | Phase 1 |
| **Why-First** | FR-011 | Why-First 阶段 | Phase 1 |
| **Why-First** | FR-012 | project-why.md 知识库 | Phase 1 |
| **Why-First** | FR-022 | project-why.md 智能维护 | Phase 2 |
| **SKILL** | FR-015 | /nomos 主 SKILL | Phase 0 |
| **Task Viewer** | FR-023 | Task Viewer HTML 界面 | Phase 1 |
| **Task Viewer** | FR-024 | 短 ID 映射系统 | Phase 1 |
| **Task Viewer** | FR-025 | 服务器自动关闭 | Phase 1 |
| **Task Viewer** | FR-026 | 动态端口分配 | Phase 1 |
| **Task Viewer** | FR-027 | .task-viewer.html 生成 | Phase 1 |
| **Task Viewer** | FR-028 | CDN 引入 marked.js/mermaid.js | Phase 1 |
| **Mermaid** | FR-013 | Mermaid 图自动生成 | Phase 1 |
| **Test-First** | FR-014 | Test-First 检查 | Phase 1 |
| **Git** | FR-036 | Gate 自动 commit | Phase 1 |
| **Git** | FR-037 | commit message 规范 | Phase 1 |
| **Git** | FR-038 | PR 描述自动生成 | Phase 2 |
| **Validator** | FR-010 | Validator Subagent | Phase 2 |

### 2.2 Should Have (P1) - 27 项

| 模块 | 需求 ID | 需求描述 | 开发阶段 |
|------|---------|----------|----------|
| **Linter** | FR-101 | Tree-sitter 多语言支持 | Phase 3 |
| **Linter** | FR-102 | Command + Prompt + Agent 混合 Handler | Phase 2 |
| **Linter** | FR-103 | plan.md 动态规则读取 | Phase 2 |
| **Linter** | FR-107 | 第三层规则示例模板 | Phase 2 |
| **Revert** | FR-104 | 果断 revert 机制 | Phase 2 |
| **Revert** | FR-110 | 失败记录到 project-why.md | Phase 2 |
| **Code Review** | FR-105 | Code Reviewer Subagent | Phase 2 |
| **Archive** | FR-106 | 任务归档 | Phase 2 |
| **Template** | FR-108 | YAML Frontmatter 支持 | Phase 0 |
| **Why-First** | FR-109 | Why-First Subagent | Phase 2 |
| **Git** | FR-111 | PR 自动生成 | Phase 2 |
| **Git** | FR-112 | 分支管理 | Phase 1 |
| **Git** | FR-113 | 自动分支创建 | Phase 1 |
| **Git** | FR-125 | commit 粒度检查 | Phase 2 |
| **Git** | FR-126 | 分支命名规范 | Phase 1 |
| **Git** | FR-127 | PR 手动触发 | Phase 2 |
| **SKILL** | FR-114 | SKILL Marketplace | Phase 2 |
| **SKILL** | FR-115 | /nomos:new-task | Phase 1 |
| **Task** | FR-116 | 任务上下文按需注入 | Phase 1 |
| **Task** | FR-117 | 任务缓存 | Phase 2 |
| **标注** | FR-118 | Honest Questioning Engine | Phase 2 |
| **标注** | FR-119 | Knowledge Similarity Detector | Phase 2 |
| **标注** | FR-120 | 知识合并操作 | Phase 2 |
| **标注** | FR-121 | 标注触发机制 | Phase 1 |
| **标注** | FR-122 | 标注状态流转 | Phase 1 |
| **标注** | FR-123 | 源码行号兜底 | Phase 1 |
| **标注** | FR-124 | WebSocket + 轮询混合刷新 | Phase 1 |

### 2.3 Could Have (P2) - 4 项

| 模块 | 需求 ID | 需求描述 | 开发阶段 |
|------|---------|----------|----------|
| **Linter** | FR-201 | YAML 配置第三层规则 | Phase 3 |
| **Linter** | FR-202 | 增量 Linter 检查 | Phase 3 |
| **Linter** | FR-203 | Linter 误报人工覆盖 | Phase 3 |
| **Linter** | FR-204 | 跨文件依赖检查 | Phase 3 |

---

## 3. 技术栈与依赖

### 3.1 核心技术栈

| 层级 | 技术 | 用途 | 版本要求 |
|------|------|------|----------|
| **前端** | HTML5/CSS3/JavaScript | Task Viewer 界面 | - |
| **前端库** | marked.js | Markdown 渲染 | v11.0+ |
| **前端库** | mermaid.js | 图表渲染 | v10.0+ |
| **后端** | Python | 服务器 + Hooks 脚本 | 3.9+ |
| **后端模块** | http.server | HTTP 服务 | 内置 |
| **后端模块** | websockets | WebSocket 通信 | 需安装 |
| **Linter** | Ruff | Python Linter | 最新版 |
| **Linter** | ESLint | JS/TS Linter | 最新版 |
| **Linter** | Bandit | Python 安全扫描 | 最新版 |
| **AST** | Tree-sitter | 多语言 AST 解析 | Phase 3 |
| **CLI** | Claude Code | 运行环境 | >= 1.0 |
| **版本控制** | Git | 代码管理 | >= 2.30 |

### 3.2 外部依赖

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         外部依赖关系                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Claude Code 平台                                                            │
│  ├── Hooks 机制 (PreToolUse/PostToolUse/Stop/SessionStart)                  │
│  ├── SKILL 系统 (/nomos)                                               │
│  └── Subagent 能力 (Validator/Reviewer)                                     │
│                                                                              │
│  Linter 工具链                                                               │
│  ├── Ruff (Python 语法/风格)                                                │
│  ├── Bandit (Python 安全)                                                   │
│  ├── ESLint (JS/TS 语法/风格)                                               │
│  └── Semgrep (通用安全扫描)                                                 │
│                                                                              │
│  CDN 资源                                                                    │
│  ├── marked.js (Markdown 解析)                                              │
│  └── mermaid.js (图表渲染)                                                  │
│                                                                              │
│  Git 生态                                                                    │
│  ├── git 命令行                                                              │
│  └── gh CLI (GitHub PR)                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 里程碑与交付物

### 4.1 里程碑定义

| 里程碑 | 阶段 | 核心交付物 | 验收标准 |
|--------|------|-----------|----------|
| **M1** | Phase 0 | MVP 版本 | 能完成一个简单任务的完整刚性流程 |
| **M2** | Phase 1 | 核心功能版 | 支持标注循环、Task Viewer、Why-First |
| **M3** | Phase 2 | 高级功能版 | 支持 Validator、Revert、智能维护 |
| **M4** | Phase 3 | 完整版 | 支持多语言、性能优化、完整配置 |

### 4.2 各阶段交付物

#### Phase 0: MVP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Phase 0 交付物 (MVP)                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Gate 0.1: 项目基础设施                                                      │
│  ├── 目录结构                                                                │
│  ├── 配置文件模板                                                            │
│  └── 文档模板                                                                │
│                                                                              │
│  Gate 0.2: Task 状态管理器                                                   │
│  ├── Task 文件夹创建/切换                                                    │
│  ├── current-task.txt 管理                                                   │
│  └── short-id-mapping.json                                                   │
│                                                                              │
│  Gate 0.3: AgentLinterEngine 核心                                            │
│  ├── BaseRule 接口                                                           │
│  ├── 第一层规则 (Ruff/ESLint 封装)                                           │
│  ├── 第二层规则 (Bandit 封装)                                                │
│  └── JSON 报告输出                                                           │
│                                                                              │
│  Gate 0.4: 基础 Hooks                                                        │
│  ├── PreToolUse Hook (Linter 检查)                                           │
│  ├── Stop Hook (Phase Gates 验证)                                            │
│  └── SessionStart Hook (轻量级提示)                                          │
│                                                                              │
│  Gate 0.5: 基础 SKILL                                                        │
│  ├── /nomos 主命令                                                      │
│  ├── /nomos:start                                                       │
│  └── /nomos:list-tasks                                                  │
│                                                                              │
│  Gate 0.6: 文档模板                                                          │
│  ├── research.md 模板                                                        │
│  ├── plan.md 模板                                                            │
│  └── code_review.md 模板                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Phase 1: Core Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Phase 1 交付物 (Core Features)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Gate 1.1: Task Viewer 基础                                                  │
│  ├── Python HTTP 服务器                                                      │
│  ├── HTML/CSS/JS 前端                                                        │
│  ├── Markdown 渲染 (marked.js)                                               │
│  ├── Mermaid 渲染 (mermaid.js)                                               │
│  ├── 动态端口分配                                                            │
│  └── 服务器自动关闭                                                          │
│                                                                              │
│  Gate 1.2: 标注系统                                                          │
│  ├── 右键创建标注                                                            │
│  ├── 左键查看历史                                                            │
│  ├── 标注历史持久化                                                          │
│  ├── 标注状态流转                                                            │
│  ├── 特殊格式标注 (代码块/Mermaid/表格)                                       │
│  └── 渲染/源码视图切换                                                       │
│                                                                              │
│  Gate 1.3: Why-First 引擎                                                    │
│  ├── Why 问题生成                                                            │
│  ├── project-why.md 管理                                                     │
│  └── Why-First 阶段门控                                                      │
│                                                                              │
│  Gate 1.4: Git 集成                                                          │
│  ├── 自动分支创建                                                            │
│  ├── Gate 自动 commit                                                        │
│  ├── commit message 规范                                                     │
│  └── 分支命名规范                                                            │
│                                                                              │
│  Gate 1.5: 任务管理增强                                                      │
│  ├── /nomos:switch-task                                                 │
│  ├── /nomos:new-task                                                    │
│  ├── /nomos:view-task                                                   │
│  ├── UserPromptSubmit Hook 智能检测                                          │
│  └── 任务上下文按需注入                                                      │
│                                                                              │
│  Gate 1.6: 内容同步                                                          │
│  ├── WebSocket 通信                                                          │
│  ├── 轮询兜底                                                                │
│  ├── 内容动态刷新                                                            │
│  └── 源码行号兜底                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Phase 2: Advanced Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Phase 2 交付物 (Advanced Features)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Gate 2.1: Validator Subagent                                                │
│  ├── research.md 审查                                                        │
│  ├── plan.md 审查                                                            │
│  ├── Protected Interfaces 检查                                               │
│  └── 审查 Checklist 管理                                                     │
│                                                                              │
│  Gate 2.2: Revert Manager                                                    │
│  ├── Revert 触发检测                                                         │
│  ├── Git Revert 执行                                                         │
│  ├── Revert 记录管理                                                         │
│  └── 教训同步到 project-why.md                                               │
│                                                                              │
│  Gate 2.3: 诚实追问引擎                                                      │
│  ├── Agent 理解检测                                                          │
│  ├── 自动追问生成                                                            │
│  └── pending_ai_question 状态管理                                            │
│                                                                              │
│  Gate 2.4: project-why.md 智能维护                                           │
│  ├── Knowledge Similarity Detector                                           │
│  ├── 知识合并操作                                                            │
│  └── 知识增强建议                                                            │
│                                                                              │
│  Gate 2.5: PR 自动生成                                                       │
│  ├── PR 描述生成                                                             │
│  ├── /nomos:pr 命令                                                     │
│  └── PR 模板管理                                                             │
│                                                                              │
│  Gate 2.6: SKILL Marketplace                                                 │
│  ├── /nomos:update-why                                                  │
│  ├── /nomos:validate                                                    │
│  ├── /nomos:archive                                                     │
│  └── 子 SKILL 调用机制                                                       │
│                                                                              │
│  Gate 2.7: 第三层规则框架                                                     │
│  ├── 第三层规则示例模板                                                      │
│  ├── plan.md 动态规则读取                                                    │
│  └── 混合 Handler 支持                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Phase 3: Optional Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Phase 3 交付物 (Optional Features)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Gate 3.1: 多语言支持                                                        │
│  ├── Tree-sitter 集成                                                        │
│  ├── 语言自动检测                                                            │
│  ├── 分语言规则集                                                            │
│  └── 多语言 AST 解析                                                         │
│                                                                              │
│  Gate 3.2: 性能优化                                                          │
│  ├── 增量 Linter 检查                                                        │
│  ├── 结果缓存                                                                │
│  ├── 并行执行                                                                │
│  └── 按需加载                                                                │
│                                                                              │
│  Gate 3.3: 配置增强                                                          │
│  ├── YAML 配置第三层规则                                                     │
│  ├── Linter 误报人工覆盖                                                     │
│  ├── 跨文件依赖检查                                                          │
│  └── 配置验证工具                                                            │
│                                                                              │
│  Gate 3.4: 文档与测试                                                        │
│  ├── 完整用户文档                                                            │
│  ├── API 文档                                                                │
│  ├── 单元测试                                                                │
│  └── 集成测试                                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 风险评估与缓解

### 5.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Claude Code Hooks API 变更 | 高 | 中 | 使用稳定的 Hooks 接口，关注官方更新 |
| Linter 工具版本兼容性 | 中 | 中 | 锁定工具版本，定期更新测试 |
| WebSocket 连接稳定性 | 中 | 低 | 实现轮询兜底机制 |
| 大型项目性能问题 | 中 | 中 | 增量检查 + 缓存 + 并行 |
| 多语言 AST 解析复杂度 | 低 | 高 | Phase 3 实现，优先主流语言 |

### 5.2 产品风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 用户学习曲线陡峭 | 高 | 中 | 提供详细文档和示例项目 |
| 标注机制不被接受 | 中 | 低 | Task Viewer 提供直观 UI |
| 与现有工作流冲突 | 中 | 中 | 支持渐进式采用 |
| 过度刚性限制灵活性 | 中 | 中 | 提供配置选项和豁免机制 |

### 5.3 缓解策略

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         风险缓解策略                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  技术风险缓解:                                                               │
│  1. 建立自动化测试体系 (单元测试 + 集成测试)                                  │
│  2. 使用 CI/CD 确保代码质量                                                  │
│  3. 定期与 Claude Code 官方版本同步测试                                       │
│  4. 建立回滚机制                                                             │
│                                                                              │
│  产品风险缓解:                                                               │
│  1. MVP 阶段收集用户反馈                                                     │
│  2. 提供完整示例项目                                                         │
│  3. 支持渐进式采用 (可只使用部分功能)                                         │
│  4. 提供配置选项平衡刚性与灵活性                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 开发文档索引

| 文档 | 描述 | 内容 |
|------|------|------|
| **07_MVP_DevPlan.md** | MVP 阶段开发计划 | Phase 0 详细设计和实现指南 |
| **08_CoreFeatures_DevPlan.md** | 核心功能开发计划 | Phase 1 详细设计和实现指南 |
| **09_AdvancedFeatures_DevPlan.md** | 高级功能开发计划 | Phase 2 详细设计和实现指南 |
| **10_OptionalFeatures_DevPlan.md** | 可选功能开发计划 | Phase 3 详细设计和实现指南 |

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| **Gate** | 阶段门控点，一个可验证的功能单元 |
| **Phase** | 开发阶段，包含多个 Gate |
| **MVP** | 最小可行产品，验证核心功能可行性 |
| **Hook** | Claude Code 生命周期钩子 |
| **SKILL** | Claude Code 技能命令 |
| **Subagent** | 子 Agent，专门负责特定任务 |
| **Review Comment** | 审查批注 |
| **Protected Interface** | 受保护的接口，不可随意修改 |

### B. 参考文档

- [02_PRD.md](02_PRD.md) - 产品需求文档
- [03_System_Architecture.md](03_System_Architecture.md) - 系统架构文档
- [04_Templates.md](04_Templates.md) - 模板文档
- [05_API_Documentation.md](05_API_Documentation.md) - API 文档

---

*最后更新: 2026-02-25*
