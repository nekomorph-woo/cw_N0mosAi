# N0mosAi Makefile
# 常用命令快捷方式

.PHONY: setup activate lint bandit clean venv help test hooks-check

# 默认目标
.DEFAULT_GOAL := help

# 虚拟环境路径
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python3
VENV_PIP := $(VENV)/bin/pip

# ====================
# 设置命令
# ====================

setup: ## 一键设置环境（创建虚拟环境并安装依赖）
	@chmod +x setup.sh
	@./setup.sh

venv: clean-venv ## 重建虚拟环境
	@echo "创建虚拟环境..."
	python3 -m venv $(VENV)
	@$(VENV_PIP) install --upgrade pip --quiet
	@$(VENV_PIP) install -r requirements.txt --quiet
	@echo "✓ 虚拟环境创建完成"

activate: ## 显示激活命令
	@echo ""
	@echo "  激活虚拟环境:"
	@echo "    source .venv/bin/activate"
	@echo ""
	@echo "  退出虚拟环境:"
	@echo "    deactivate"
	@echo ""

# ====================
# Linter 命令
# ====================

lint: ## 运行 ruff 检查
	@if [ -f "$(VENV_PYTHON)" ]; then \
		$(VENV)/bin/ruff check .claude/hooks/lib/ --exclude __pycache__; \
	else \
		echo "⚠ 虚拟环境未创建，运行 'make setup'"; \
	fi

bandit: ## 运行安全扫描
	@if [ -f "$(VENV)/bin/bandit" ]; then \
		$(VENV)/bin/bandit -r .claude/hooks/lib/ -ll --exclude __pycache__; \
	else \
		echo "⚠ bandit 未安装"; \
	fi

security: bandit ## 运行安全扫描 (别名)

# ====================
# 测试命令
# ====================

test: ## 运行单元测试
	@if [ -d "tests" ]; then \
		$(VENV_PYTHON) -m pytest tests/ -v; \
	else \
		echo "⚠ tests/ 目录不存在"; \
	fi

# ====================
# Hooks 验证
# ====================

hooks-check: ## 验证 Hooks 脚本是否可执行
	@echo "检查 Hooks 脚本..."
	@for hook in .claude/hooks/*.sh; do \
		if [ -x "$$hook" ]; then \
			echo "  ✓ $$hook (可执行)"; \
		else \
			echo "  ✗ $$hook (不可执行)"; \
			chmod +x "$$hook"; \
			echo "    → 已修复"; \
		fi; \
	done

hooks-test: hooks-check ## 测试 Hooks 是否正常工作
	@echo ""
	@echo "测试 SessionStart Hook:"
	@.claude/hooks/nomos-session-start.sh
	@echo ""
	@echo "测试 PreToolUse Hook (正常代码):"
	@echo '{"file_path": "test.py", "content": "x = 1"}' | .claude/hooks/nomos-pretooluse.sh
	@echo ""
	@echo "测试 Stop Hook:"
	@.claude/hooks/nomos-stop.sh

# ====================
# 清理命令
# ====================

clean: ## 清理缓存文件
	@echo "清理缓存文件..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf .claude/cache/* 2>/dev/null || true
	@echo "✓ 清理完成"

clean-venv: ## 删除虚拟环境
	@echo "删除虚拟环境..."
	@rm -rf $(VENV)
	@echo "✓ 虚拟环境已删除"

clean-all: clean clean-venv ## 清理所有（包括虚拟环境）
	@echo "✓ 全部清理完成"

# ====================
# 帮助
# ====================

help: ## 显示帮助信息
	@echo ""
	@echo "N0mosAi Makefile 命令"
	@echo ""
	@echo "  设置命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-15s\033[0m %s\n", $$1, $$2}' | head -5
	@echo ""
	@echo "  Linter 命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-15s\033[0m %s\n", $$1, $$2}' | sed -n '6,8p'
	@echo ""
	@echo "  测试命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-15s\033[0m %s\n", $$1, $$2}' | sed -n '9,11p'
	@echo ""
	@echo "  清理命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-15s\033[0m %s\n", $$1, $$2}' | tail -4
	@echo ""
