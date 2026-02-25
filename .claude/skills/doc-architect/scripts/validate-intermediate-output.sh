#!/bin/bash
# validate-intermediate-output.sh
# Fixed version for Git Bash compatibility

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default directory
DOCS_DIR="${1:-./doc-arch}"

echo "════════════════════════════════════════════════════════════════"
echo "         DOC-ARCHITECT INTERMEDIATE OUTPUT VALIDATOR"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Validating directory: $DOCS_DIR"
echo ""

# Check if doc-arch directory exists
if [ ! -d "$DOCS_DIR" ]; then
    echo -e "${RED}✗ Error: Directory '$DOCS_DIR' does not exist${NC}"
    exit 1
fi

# Track validation results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to validate 00_Key_Points_List.md
validate_key_points() {
    local file="$DOCS_DIR/00_Key_Points_List.md"
    echo "Checking: 00_Key_Points_List.md"

    if [ ! -f "$file" ]; then
        echo -e "  ${RED}✗ File not found${NC}"
        ((FAILED_CHECKS++))
        return
    fi

    ((TOTAL_CHECKS++))

    # Check for required sections
    local required_sections=("Keywords" "New Concepts" "Decision Points" "Question Points")
    local all_present=true

    for section in "${required_sections[@]}"; do
        if grep -q "^## $section" "$file"; then
            echo -e "  ${GREEN}✓${NC} Section '$section' found"
        else
            echo -e "  ${RED}✗${NC} Section '$section' missing"
            all_present=false
        fi
    done

    # Check for list items using sed instead of awk
    for section in "${required_sections[@]}"; do
        # Get next section name to use as end marker
        local next_section=""
        case "$section" in
            "Keywords") next_section="New Concepts" ;;
            "New Concepts") next_section="Decision Points" ;;
            "Decision Points") next_section="Question Points" ;;
            "Question Points") next_section="$" ;;  # End of file
        esac

        # Use sed to extract section and check for list items
        if sed -n "/^## $section/,/^## ${next_section}/p" "$file" | grep -q "^- "; then
            ((PASSED_CHECKS++))
        else
            echo -e "  ${YELLOW}⚠${NC} Section '$section' has no list items"
        fi
    done

    if $all_present; then
        echo -e "  ${GREEN}✓ All required sections present${NC}"
        ((PASSED_CHECKS++))
    else
        ((FAILED_CHECKS++))
    fi

    echo ""
}

# Function to validate 01_Structured_Notes.md
validate_structured_notes() {
    local file="$DOCS_DIR/01_Structured_Notes.md"
    echo "Checking: 01_Structured_Notes.md"

    if [ ! -f "$file" ]; then
        echo -e "  ${RED}✗ File not found${NC}"
        ((FAILED_CHECKS++))
        return
    fi

    ((TOTAL_CHECKS++))

    # Check for required dimensions
    local required_dimensions=("Business / Value" "Technical / Architecture" "Specs / Constraints")
    local all_present=true

    for dimension in "${required_dimensions[@]}"; do
        if grep -q "\[Dimension.*$dimension\]" "$file"; then
            echo -e "  ${GREEN}✓${NC} Dimension '$dimension' found"
        else
            echo -e "  ${RED}✗${NC} Dimension '$dimension' missing"
            all_present=false
        fi
    done

    # Check for sub-sections
    local expected_subsections=(
        "Pain Points"
        "Core Interaction"
        "Value Proposition"
        "Data Flow"
        "Key Components"
        "Constraints"
        "Input/Output"
    )

    local subsection_count=0
    for subsection in "${expected_subsections[@]}"; do
        if grep -q "### $subsection" "$file"; then
            ((subsection_count++))
        fi
    done

    echo -e "  Found $subsection_count/${#expected_subsections[@]} expected subsections"

    if $all_present; then
        echo -e "  ${GREEN}✓ All required dimensions present${NC}"
        ((PASSED_CHECKS++))
    else
        ((FAILED_CHECKS++))
    fi

    echo ""
}

# Function to validate 99_Value_Details.md
validate_value_details() {
    local file="$DOCS_DIR/99_Value_Details.md"
    echo "Checking: 99_Value_Details.md"

    if [ ! -f "$file" ]; then
        echo -e "  ${RED}✗ File not found${NC}"
        ((FAILED_CHECKS++))
        return
    fi

    ((TOTAL_CHECKS++))

    # Check for Generation Context
    if grep -q "## Generation Context" "$file" || grep -q "## 生成上下文" "$file"; then
        echo -e "  ${GREEN}✓${NC} Generation Context found"
    else
        echo -e "  ${YELLOW}⚠${NC} Generation Context missing (recommended)"
    fi

    # Check for value categories
    local categories=(
        "Future Considerations"
        "Alternative Approaches"
        "Implementation Details"
        "User Insights"
        "Edge Cases"
        "Dependencies"
        "Open Questions"
    )

    local category_count=0
    for category in "${categories[@]}"; do
        if grep -q "## $category" "$file"; then
            ((category_count++))
        fi
    done

    echo -e "  Found $category_count/${#categories[@]} value categories"

    # Check for table format
    if grep -q "^|" "$file"; then
        echo -e "  ${GREEN}✓${NC} Table format detected"
        ((PASSED_CHECKS++))
    else
        echo -e "  ${YELLOW}⚠${NC} No table format found (expected markdown tables)"
    fi

    if [ $category_count -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} Value categories present"
        ((PASSED_CHECKS++))
    else
        echo -e "  ${RED}✗${NC} No value categories found"
        ((FAILED_CHECKS++))
    fi

    echo ""
}

# Run validation
validate_key_points
validate_structured_notes
validate_value_details

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "                         VALIDATION SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Total Checks:  $TOTAL_CHECKS"
echo -e "Passed:       ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed:       ${RED}$FAILED_CHECKS${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some validations failed. Please review the output above.${NC}"
    exit 1
fi
