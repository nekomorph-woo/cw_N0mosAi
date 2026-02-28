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

#### Python Linter (Layer 1 语法 + Layer 2 安全)

```bash
pip install ruff bandit
```

#### JavaScript/TypeScript Linter (Layer 1 语法 + Layer 2 安全)

```bash
# 方式 1: 全局安装
npm install -g eslint eslint-plugin-security

# 方式 2: 项目本地安装 (推荐)
npm install --save-dev eslint eslint-plugin-security
```

> ⚠️ **注意**: JS/TS 安全检查需要 `eslint-plugin-security` 插件

#### Tree-sitter (多语言语法支持)

```bash
# Python 3.12 及以下
pip install tree-sitter tree-sitter-languages

# Python 3.13+ (使用新版 API)
pip install tree-sitter
pip install tree-sitter-go tree-sitter-java tree-sitter-rust  # 按需安装
```

#### 依赖对照表

| 语言 | Layer 1 语法 | Layer 2 安全 | 安装命令 |
|------|-------------|-------------|----------|
| Python | ruff | bandit | `pip install ruff bandit` |
| JS/TS | eslint | eslint-plugin-security | `npm install eslint eslint-plugin-security` |
| Go | tree-sitter-go | gosec (需单独安装) | `pip install tree-sitter-go` |
| Java | tree-sitter-java | SpotBugs (需单独安装) | `pip install tree-sitter-java` |
| Rust | tree-sitter-rust | cargo-audit (需单独安装) | `pip install tree-sitter-rust` |

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
