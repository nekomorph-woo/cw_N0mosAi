# Execution Report Format

This document defines the standard format for Phase 6 (Execution Report) output, ensuring consistent and comprehensive reporting of the doc-architect workflow results.

---

## Report Structure

The execution report should be printed to the console/output in the following format:

```
════════════════════════════════════════════════════════════════
                  DOC-ARCHITECT EXECUTION REPORT
════════════════════════════════════════════════════════════════

Input:          [INPUT_FILE]
Template:       [A/B/C]
Output Dir:     [OUTPUT_DIR]
Generated:      [DATE]
Duration:       [APPROXIMATE_TIME]

════════════════════════════════════════════════════════════════
                         1. FILE CREATION SUMMARY
════════════════════════════════════════════════════════════════

✓ Intermediate Products Created:
  • 00_Key_Points_List.md (Raw extraction)
  • 01_Structured_Notes.md (Categorized extraction)

✓ Final Documents Created: [N]
  • [Document 1]
  • [Document 2]
  • [Document 3]

✓ Final Documents Updated: [N]
  • [Document 1] (Merge statistics below)
  • [Document 2] (Merge statistics below)

✓ Value Details Document (Mandatory):
  • 99_Value_Details.md
    - Future Considerations: [N] items
    - Alternative Approaches: [N] items
    - Implementation Details: [N] items
    - User Insights: [N] items
    - Edge Cases: [N] items
    - Dependencies: [N] items
    - Open Questions: [N] items

Total Files Generated/Updated: [N]

════════════════════════════════════════════════════════════════
                          2. DIFF SUMMARY
════════════════════════════════════════════════════════════════

[For each updated file, show:]

▶ [filename.md]
  Sections Added:      [N]
  Sections Modified:   [N]
  Sections Deleted:    [N]
  Sections Unchanged:  [N]

  Key Changes:
  + [Brief description of major addition]
  ~ [Brief description of major modification]
  - [Brief description of major deletion]

════════════════════════════════════════════════════════════════
                          3. QUALITY REPORT
════════════════════════════════════════════════════════════════

Validation Results:
  Errors Corrected:         [N] items
  Omissions Supplemented:   [N] items
  Contradictions Resolved:  [N] items
  Cross-Document Conflicts: [N] items

Value Details Capture:
  Total Items Analyzed:     [N]
  Valuable Items Captured:  [N]
  Capture Rate:            [N]%

════════════════════════════════════════════════════════════════
                          4. ACTION ITEMS
════════════════════════════════════════════════════════════════

Manual Review Points:
  [ ] [Review point 1]
  [ ] [Review point 2]
  [ ] [Review point 3]

Information Still Needed:
  [ ] [Missing info 1]
  [ ] [Missing info 2]

Open Questions Requiring Attention:
  [P0] [Critical question if any]
  [P1] [High-priority question if any]

Recommended Next Steps:
  1. [Recommended action 1]
  2. [Recommended action 2]
  3. [Recommended action 3]

════════════════════════════════════════════════════════════════
                            SUMMARY
════════════════════════════════════════════════════════════════

Status: [SUCCESS / SUCCESS_WITH_WARNINGS / NEEDS_ATTENTION]

All documents have been generated in: [OUTPUT_DIR]
Intermediate products available for review.
Value details preserved in: 99_Value_Details.md

For questions or issues, refer to:
  • Original input: [INPUT_FILE]
  • Intermediate: 00_Key_Points_List.md, 01_Structured_Notes.md
  • Value details: 99_Value_Details.md

════════════════════════════════════════════════════════════════
```

---

## Report Sections Explained

### 1. File Creation Summary

**Purpose:** Provide overview of all files created/updated

**Fields:**
- `Intermediate Products` - Always 2 files (00_, 01_)
- `Final Documents Created` - New files from template
- `Final Documents Updated` - Existing files with merges
- `Value Details Document` - Always 1 file (99_)

**Quality Check:** Ensure counts match actual operations

---

### 2. Diff Summary

**Purpose:** Show what changed in updated files

**For Each Updated File:**

| Field | Description | Example |
|-------|-------------|---------|
| Sections Added | New sections created | 3 |
| Sections Modified | Existing sections changed | 5 |
| Sections Deleted | Sections removed | 1 |
| Sections Unchanged | Sections preserved | 12 |

**Key Changes:** Brief description of major changes (2-4 bullet points)

**Quality Check:** Ensure changes align with Structured Notes

---

### 3. Quality Report

**Purpose:** Report on validation and quality assurance activities

**Validation Results:**

| Metric | Description | Target |
|--------|-------------|--------|
| Errors Corrected | Misinterpretations fixed | Minimize |
| Omissions Supplemented | Missing content added | Minimize |
| Contradictions Resolved | Inconsistencies fixed | Minimize |
| Cross-Document Conflicts | Inter-document issues | 0 ideal |

**Value Details Capture:**

| Metric | Description | Calculation |
|--------|-------------|-------------|
| Total Items Analyzed | Items from Structured Notes | Count |
| Valuable Items Captured | Items in 99_Value_Details.md | Count |
| Capture Rate | Percentage of valuable items preserved | (Captured / Analyzed) × 100 |

**Quality Check:** High capture rate (>80%) for valuable items

---

### 4. Action Items

**Purpose:** Identify follow-up activities

**Manual Review Points:**
- Content requiring human judgment
- Ambiguous or uncertain items
- Business decisions needed

**Information Still Needed:**
- Gaps in understanding
- Missing context or details
- Unclear requirements

**Open Questions Requiring Attention:**
- P0 (Critical): Blocks progress
- P1 (High): Important but not blocking
- P2+ (Medium/Low): Nice to resolve

**Recommended Next Steps:**
- Concrete actions to take
- Prioritized by importance
- Actionable and specific

---

### Summary

**Purpose:** Quick status overview and reference

**Status Levels:**

| Status | Condition | User Action |
|--------|-----------|-------------|
| SUCCESS | All clean, no issues | Review at leisure |
| SUCCESS_WITH_WARNINGS | Minor issues found | Review warnings |
| NEEDS_ATTENTION | Critical issues found | Address immediately |

---

## Report Generation Timing

The report should be generated:

1. **After Phase 5-B completion** - After all validation
2. **Before user interaction** - Ready for immediate display
3. **With duration estimate** - Help user understand processing time

---

## Report Output Methods

### Console Output (Primary)

```
Print the full formatted report to console
```

### File Output (Optional)

If requested by user, also save to:

```
OUTPUT_DIR/00_Execution_Report_[TIMESTAMP].md
```

---

## Quality Metrics

### Target Metrics

| Metric | Target | Acceptable |
|--------|--------|------------|
| Capture Rate | >90% | >80% |
| Cross-Document Conflicts | 0 | <3 |
| Unresolved P0 Questions | 0 | 0 |
| Manual Review Points | <5 | <10 |

### Warning Thresholds

Trigger warnings when:

- Capture Rate < 80%
- Cross-Document Conflicts > 3
- P0 Questions > 0
- Manual Review Points > 10

---

## Template Strings

Use these template strings for consistent formatting:

```python
# File creation summary
FILE_CREATED = "✓ {filename}: {description}"
FILE_UPDATED = "• {filename} ({merge_stats})"

# Diff summary
DIFF_HEADER = "▶ {filename}"
DIFF_STAT = "  {key}: {value}"

# Quality metrics
QUALITY_METRIC = "  {metric}: {value} items"
CAPTURE_RATE = "  Capture Rate: {rate}%"

# Action items
REVIEW_POINT = "  [ ] {point}"
INFO_NEEDED = "  [ ] {info}"
OPEN_QUESTION = "  [{priority}] {question}"

# Status
SUCCESS = "✓ SUCCESS"
WARNING = "⚠ SUCCESS_WITH_WARNINGS"
ATTENTION = "✗ NEEDS_ATTENTION"
```

---

## Error Handling

### Report Generation Failures

If report generation fails:

1. Print simplified error report
2. Include error details
3. Recommend manual review
4. Log error for debugging

### Simplified Error Report

```
════════════════════════════════════════════════════════════════
                    DOC-ARCHITECT ERROR REPORT
════════════════════════════════════════════════════════════════

Status: ERROR

Error: [ERROR_MESSAGE]
Files Generated: [LIST]
Files Failed: [LIST]

Recommendation: Review generated files and re-run if needed.

════════════════════════════════════════════════════════════════
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.5.0 | [DATE] | Initial format definition for doc-architect skill |
