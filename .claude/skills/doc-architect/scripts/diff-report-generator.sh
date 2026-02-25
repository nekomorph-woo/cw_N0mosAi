#!/bin/bash
# diff-report-generator.sh
# Generates a diff report comparing old and new versions of documents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
OLD_DIR="${1:-./doc-arch.old}"
NEW_DIR="${2:-./doc-arch}"
OUTPUT_FILE="${3:-./doc-arch/diff-report.md}"

echo "════════════════════════════════════════════════════════════════"
echo "              DOC-ARCHITECT DIFF REPORT GENERATOR"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Old Directory: $OLD_DIR"
echo "New Directory: $NEW_DIR"
echo "Output File:   $OUTPUT_FILE"
echo ""

# Check if directories exist
if [ ! -d "$OLD_DIR" ]; then
    echo -e "${RED}✗ Error: Old directory '$OLD_DIR' does not exist${NC}"
    echo "  This is expected for first-time generation."
    echo "  Creating a minimal report..."
    NO_OLD=true
fi

if [ ! -d "$NEW_DIR" ]; then
    echo -e "${RED}✗ Error: New directory '$NEW_DIR' does not exist${NC}"
    exit 1
fi

# Function to count lines in a file
count_lines() {
    local file="$1"
    if [ -f "$file" ]; then
        wc -l < "$file" | tr -d ' '
    else
        echo "0"
    fi
}

# Function to get file size
get_size() {
    local file="$1"
    if [ -f "$file" ]; then
        wc -c < "$file" | tr -d ' '
    else
        echo "0"
    fi
}

# Function to count sections (markdown headers)
count_sections() {
    local file="$1"
    if [ -f "$file" ]; then
        grep -c "^#" "$file" || echo "0"
    else
        echo "0"
    fi
}

# Generate report
generate_report() {
    local report_file="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    cat > "$report_file" << EOF
# Document Generation Diff Report

**Generated:** $timestamp
**Old Directory:** \`$OLD_DIR\`
**New Directory:** \`$NEW_DIR\`

---

## Summary

EOF

    if [ "$NO_OLD" = true ]; then
        cat >> "$report_file" << EOF
This is the first document generation. No comparison with previous version available.

EOF
    fi

    # Get list of files in new directory
    local new_files=$(find "$NEW_DIR" -name "*.md" -type f | sort)

    if [ -z "$new_files" ]; then
        echo "No markdown files found in $NEW_DIR" >&2
        exit 1
    fi

    # File comparison table
    cat >> "$report_file" << EOF
## File Statistics

| File | Lines Old | Lines New | Sections Old | Sections New | Status |
|------|-----------|-----------|--------------|--------------|--------|
EOF

    local total_added=0
    local total_modified=0
    local total_created=0

    while IFS= read -r new_file; do
        local basename=$(basename "$new_file")
        local old_file="$OLD_DIR/$basename"

        local lines_new=$(count_lines "$new_file")
        local lines_old=$(count_lines "$old_file")
        local sections_new=$(count_sections "$new_file")
        local sections_old=$(count_sections "$old_file")

        local status=""
        if [ "$lines_old" = "0" ]; then
            status="${GREEN}CREATED${NC}"
            ((total_created++))
        elif [ "$lines_new" -gt "$lines_old" ]; then
            status="${GREEN}EXPANDED${NC}"
            ((total_modified++))
        elif [ "$lines_new" -lt "$lines_old" ]; then
            status="${YELLOW}REDUCED${NC}"
            ((total_modified++))
        else
            status="${BLUE}UNCHANGED${NC}"
        fi

        # Remove color codes for file output
        local status_plain=$(echo "$status" | sed 's/\x1b\[[0-9;]*m//g')

        echo "| \`$basename\` | $lines_old | $lines_new | $sections_old | $sections_new | $status_plain |" >> "$report_file"

    done <<< "$new_files"

    # Detailed analysis for each file
    cat >> "$report_file" << EOF

---

## Detailed Analysis

EOF

    while IFS= read -r new_file; do
        local basename=$(basename "$new_file")
        local old_file="$OLD_DIR/$basename"

        cat >> "$report_file" << EOF
### \`$basename\`

EOF

        if [ "$NO_OLD" = true ] || [ ! -f "$old_file" ]; then
            echo "**Status:** New file created" >> "$report_file"
            echo "" >> "$report_file"
            echo "**Statistics:**" >> "$report_file"
            echo "- Lines: $lines_new" >> "$report_file"
            echo "- Sections: $sections_new" >> "$report_file"
            echo "- Size: $(get_size "$new_file") bytes" >> "$report_file"
        else
            # Generate actual diff
            local diff_output=$(diff -u "$old_file" "$new_file" 2>/dev/null || true)

            if [ -z "$diff_output" ]; then
                echo "**Status:** No changes detected" >> "$report_file"
            else
                local added_lines=$(echo "$diff_output" | grep -c "^+" || echo "0")
                local removed_lines=$(echo "$diff_output" | grep -c "^-" || echo "0")

                echo "**Status:** Modified" >> "$report_file"
                echo "" >> "$report_file"
                echo "**Changes:**" >> "$report_file"
                echo "- Lines added: ~$added_lines" >> "$report_file"
                echo "- Lines removed: ~$removed_lines" >> "$report_file"
                echo "" >> "$report_file"
                echo "**Diff Preview:**" >> "$report_file"
                echo '```diff' >> "$report_file"

                # Add limited diff preview (first 50 lines)
                echo "$diff_output" | head -n 50 >> "$report_file"

                if [ $(echo "$diff_output" | wc -l) -gt 50 ]; then
                    echo "" >> "$report_file"
                    echo "... (diff truncated, use \`diff -u $old_file $new_file\` for full output)" >> "$report_file"
                fi

                echo '```' >> "$report_file"
            fi
        fi

        echo "" >> "$report_file"
        echo "---" >> "$report_file"
        echo "" >> "$report_file"

    done <<< "$new_files"

    # Summary section
    cat >> "$report_file" << EOF
---

## Generation Summary

- **Files Created:** $total_created
- **Files Modified:** $total_modified
- **Total Files:** $(echo "$new_files" | wc -l)

### Recommendations

1. Review modified files for accuracy
2. Verify that new content aligns with original input
3. Check 99_Value_Details.md for important long-tail content
4. Run validation: \`./scripts/validate-intermediate-output.sh\`

---

*This report was auto-generated by doc-architect diff-report-generator.sh*
EOF
}

# Generate the report
generate_report "$OUTPUT_FILE"

# Print console summary
echo -e "${GREEN}✓${NC} Diff report generated: $OUTPUT_FILE"
echo ""
echo "Report contents:"
echo "  • File statistics comparison"
echo "  • Detailed diff analysis"
echo "  • Change summaries"
echo ""
echo "To view the report:"
echo "  cat $OUTPUT_FILE"
echo "  or"
echo "  less $OUTPUT_FILE"
echo ""

# Also print summary to console
echo "════════════════════════════════════════════════════════════════"
echo "                      CONSOLE SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ "$NO_OLD" != true ]; then
    # Quick file-by-file comparison
    echo "File Changes:"
    echo "────────────────────────────────────────────────────────────"

    for new_file in "$NEW_DIR"/*.md; do
        if [ -f "$new_file" ]; then
            basename=$(basename "$new_file")
            old_file="$OLD_DIR/$basename"

            if [ -f "$old_file" ]; then
                old_lines=$(count_lines "$old_file")
                new_lines=$(count_lines "$new_file")
                diff=$((new_lines - old_lines))

                if [ $diff -gt 0 ]; then
                    echo -e "  ${GREEN}+$basename${NC}: +$diff lines"
                elif [ $diff -lt 0 ]; then
                    echo -e "  ${YELLOW}$basename${NC}: $diff lines"
                else
                    echo -e "  ${BLUE}=$basename${NC}: unchanged"
                fi
            else
                echo -e "  ${GREEN}+$basename${NC}: new file"
            fi
        fi
    done
else
    echo "New files created:"
    echo "────────────────────────────────────────────────────────────"
    for new_file in "$NEW_DIR"/*.md; do
        if [ -f "$new_file" ]; then
            basename=$(basename "$new_file")
            lines=$(count_lines "$new_file")
            echo -e "  ${GREEN}+$basename${NC}: $lines lines"
        fi
    done
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
