#!/bin/bash
# nOmOsAi 一键设置脚本
# 创建虚拟环境并安装所有依赖

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    nOmOsAi 环境设置                               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: 检查 Python 版本
echo -e "${YELLOW}[1/5] 检查 Python 版本...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}✗ Python 版本过低: $PYTHON_VERSION (需要 3.8+)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 版本: $PYTHON_VERSION${NC}"

# Step 2: 创建虚拟环境
echo ""
echo -e "${YELLOW}[2/5] 创建虚拟环境...${NC}"
if [ -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}  虚拟环境已存在，跳过创建${NC}"
else
    python3 -m venv "$VENV_PATH"
    echo -e "${GREEN}✓ 虚拟环境创建成功: $VENV_PATH${NC}"
fi

# Step 3: 激活虚拟环境
echo ""
echo -e "${YELLOW}[3/5] 激活虚拟环境...${NC}"
source "$VENV_PATH/bin/activate"
echo -e "${GREEN}✓ 虚拟环境已激活${NC}"

# Step 4: 安装依赖
echo ""
echo -e "${YELLOW}[4/5] 安装 Python 依赖...${NC}"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install --upgrade pip --quiet

    # 尝试多种安装方式
    echo "  尝试使用清华镜像源..."
    if pip install -r "$PROJECT_ROOT/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet 2>/dev/null; then
        echo -e "${GREEN}✓ 依赖安装完成 (清华镜像)${NC}"
    else
        echo "  清华镜像失败，尝试信任主机..."
        if pip install -r "$PROJECT_ROOT/requirements.txt" --trusted-host pypi.org --trusted-host files.pythonhosted.org --quiet 2>/dev/null; then
            echo -e "${GREEN}✓ 依赖安装完成 (信任主机)${NC}"
        else
            echo "  信任主机失败，尝试阿里云镜像..."
            if pip install -r "$PROJECT_ROOT/requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --quiet 2>/dev/null; then
                echo -e "${GREEN}✓ 依赖安装完成 (阿里云镜像)${NC}"
            else
                echo -e "${RED}✗ 依赖安装失败，请检查网络连接${NC}"
                echo -e "${YELLOW}  你可以手动运行以下命令尝试安装:${NC}"
                echo "  pip install pyyaml ruff bandit -i https://pypi.tuna.tsinghua.edu.cn/simple"
                exit 1
            fi
        fi
    fi
else
    echo -e "${RED}✗ 找不到 requirements.txt${NC}"
    exit 1
fi

# Step 5: 验证安装
echo ""
echo -e "${YELLOW}[5/5] 验证安装...${NC}"

SUCCESS=true

# 检查 pyyaml
if python3 -c "import yaml" 2>/dev/null; then
    echo -e "${GREEN}  ✓ pyyaml${NC}"
else
    echo -e "${RED}  ✗ pyyaml 未安装${NC}"
    SUCCESS=false
fi

# 检查 ruff
if command -v ruff &> /dev/null; then
    RUFF_VERSION=$(ruff --version | head -1)
    echo -e "${GREEN}  ✓ ruff ($RUFF_VERSION)${NC}"
else
    echo -e "${YELLOW}  ⚠ ruff 未安装 (可选)${NC}"
fi

# 检查 bandit
if command -v bandit &> /dev/null; then
    BANDIT_VERSION=$(bandit --version | head -1)
    echo -e "${GREEN}  ✓ bandit ($BANDIT_VERSION)${NC}"
else
    echo -e "${YELLOW}  ⚠ bandit 未安装 (可选)${NC}"
fi

# 检查 Node.js 依赖 (JS/TS 安全检查)
if command -v npm &> /dev/null; then
    echo -e "${GREEN}  ✓ npm 已安装${NC}"
    # 检查 eslint-plugin-security
    if [ -f "$PROJECT_ROOT/node_modules/eslint-plugin-security/package.json" ]; then
        echo -e "${GREEN}  ✓ eslint-plugin-security${NC}"
    else
        echo -e "${YELLOW}  ⚠ eslint-plugin-security 未安装${NC}"
        echo -e "${YELLOW}    运行: npm install (在项目根目录)${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ npm 未安装 (JS/TS 检查将跳过)${NC}"
fi

# 完成
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
if [ "$SUCCESS" = true ]; then
    echo -e "${GREEN}║                    ✓ 设置完成！                                   ║${NC}"
else
    echo -e "${YELLOW}║                    ⚠ 设置完成（部分可选组件缺失）                  ║${NC}"
fi
echo -e "${BLUE}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║                                                                   ${NC}"
echo -e "${BLUE}║  日常使用:                                                        ${NC}"
echo -e "${BLUE}║    source .venv/bin/activate    # 激活虚拟环境                   ${NC}"
echo -e "${BLUE}║                                                                   ${NC}"
echo -e "${BLUE}║  或使用 Makefile:                                                 ${NC}"
echo -e "${BLUE}║    make activate                # 显示激活命令                   ${NC}"
echo -e "${BLUE}║    make lint                    # 运行 Linter                    ${NC}"
echo -e "${BLUE}║    make clean                   # 清理缓存                       ${NC}"
echo -e "${BLUE}║                                                                   ${NC}"
echo -e "${BLUE}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║  JS/TS 安全检查依赖 (可选):                                       ${NC}"
echo -e "${BLUE}║    npm install                    # 安装 eslint + security 插件   ${NC}"
echo -e "${BLUE}║                                                                   ${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
