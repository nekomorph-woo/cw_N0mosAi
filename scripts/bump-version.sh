#!/bin/bash
# nOmOsAi 版本更新脚本
# 更新所有版本号到指定版本
#
# 用法: ./scripts/bump-version.sh <version>
# 示例: ./scripts/bump-version.sh 0.2.0
#
# 修改的文件:
#   1. .claude/settings.json       → nomos.version
#   2. .claude/skills/nomos/SKILL.md → version (YAML frontmatter)
#   3. .claude/hooks/lib/__init__.py → __version__

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 版本号验证
VERSION="$1"
if [ -z "$VERSION" ]; then
    echo -e "${RED}错误: 请提供版本号${NC}"
    echo "用法: $0 <version>"
    echo "示例: $0 0.2.0"
    exit 1
fi

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}错误: 版本号格式无效，应为 X.Y.Z (如 0.2.0)${NC}"
    exit 1
fi

echo -e "${YELLOW}=== nOmOsAi 版本更新 ===${NC}"
echo "目标版本: $VERSION"
echo ""

# 1. 更新 settings.json
SETTINGS_FILE="$PROJECT_ROOT/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    if command -v python3 &> /dev/null; then
        python3 -c "
import json
with open('$SETTINGS_FILE', 'r') as f:
    data = json.load(f)
data['nomos']['version'] = '$VERSION'
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"
        echo -e "${GREEN}✓${NC} settings.json → nomos.version: $VERSION"
    else
        echo -e "${RED}✗${NC} 需要 python3 来更新 JSON 文件"
    fi
else
    echo -e "${YELLOW}⚠${NC} settings.json 不存在，跳过"
fi

# 2. 更新 SKILL.md
SKILL_FILE="$PROJECT_ROOT/.claude/skills/nomos/SKILL.md"
if [ -f "$SKILL_FILE" ]; then
    sed -i.bak "s/^version: .*$/version: $VERSION/" "$SKILL_FILE"
    rm -f "${SKILL_FILE}.bak"
    echo -e "${GREEN}✓${NC} SKILL.md → version: $VERSION"
else
    echo -e "${YELLOW}⚠${NC} SKILL.md 不存在，跳过"
fi

# 3. 更新 __init__.py
INIT_FILE="$PROJECT_ROOT/.claude/hooks/lib/__init__.py"
if [ -f "$INIT_FILE" ]; then
    sed -i.bak "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" "$INIT_FILE"
    rm -f "${INIT_FILE}.bak"
    echo -e "${GREEN}✓${NC} __init__.py → __version__: $VERSION"
else
    echo -e "${YELLOW}⚠${NC} __init__.py 不存在，跳过"
fi

echo ""
echo -e "${GREEN}=== 版本更新完成 ===${NC}"
echo ""
echo "修改的文件:"
echo "  - .claude/settings.json"
echo "  - .claude/skills/nomos/SKILL.md"
echo "  - .claude/hooks/lib/__init__.py"
echo ""
echo "下一步: git add -A && git commit -m 'chore: bump version to $VERSION'"
