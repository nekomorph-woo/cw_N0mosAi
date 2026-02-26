# CLAUDE.md - 项目指南

本文档记录 Claude Code 在本项目中的工作规范和约定。

---

## 1. 项目信息

| 项目 | 说明 |
|------|------|
| 品牌 | N0mosAi |
| 内部名 | Nomos (希腊语 νόμος，法则) |
| CLI 前缀 | `/nomos` |

---

## 2. 术语约定

| 术语 | 含义 |
|------|------|
| Agent | AI 智能体（如 Claude） |
| Hook | Claude Code 生命周期钩子 |
| Phase | 阶段（Why-First/Research/Plan/Execute/Review） |
| Gate | 阶段门控点 |
| 标注 | 人类在文档中的批注 |

---

## 3. 目录结构

```
cw_N0mosAi/
├── CLAUDE.md                    # 项目指南（本文件）
├── .claude/
│   ├── hooks/                   # Hooks 脚本
│   ├── skills/nomos/            # N0mosAi SKILL
│   ├── rules/                   # 规则配置
│   │   ├── nomos-style.md       # 输出规范（自动注入）
│   │   ├── languages.yml        # 多语言配置
│   │   └── ignore.yml           # 豁免规则
│   └── settings.json            # Claude Code 设置
├── doc-arch/agent-nomos-flow/   # 项目文档
└── tasks/                       # 任务文件夹
```

---

## 4. 快速开始

```bash
# 设置环境
./setup.sh

# 激活虚拟环境
source .venv/bin/activate

# 开始新任务
/nomos:start <任务名>

# 查看帮助
make help
```

---

*输出规范（绘图、Emoji、表格等）已内化到系统，通过 SessionStart Hook 自动注入。*
