# nOmOsAi 安装指南

## 环境要求

- Python 3.8+
- Git 2.0+
- Claude Code CLI

## 安装步骤

### 1. 克隆仓库

```bash
git clone <repository-url>
cd cw_nOmOsAi
```

### 2. 安装依赖

```bash
pip install pyyaml
```

### 3. 可选依赖

```bash
# Python Linter
pip install ruff bandit

# JavaScript/TypeScript Linter
npm install -g eslint

# Tree-sitter (多语言支持)
pip install tree-sitter tree-sitter-languages
```

### 4. 配置

nOmOsAi 使用 `.claude/` 目录存储配置和 Hooks。

主要配置文件:
- `.claude/settings.json`: Claude Code 设置
- `.claude/rules/languages.yml`: 多语言配置
- `.claude/rules/ignore.yml`: 豁免规则配置

## 验证安装

```bash
# 检查 Python 版本
python --version

# 检查 Git 版本
git --version

# 检查可选工具
ruff --version
eslint --version
```

## 下一步

参见 [快速开始](quickstart.md) 了解如何使用 nOmOsAi。
