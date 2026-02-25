# Doc Architect Skill

**Version:** 0.5.3
**Status:** Beta
**Author:** Generated for Claude Code CLI

---

## Overview

`doc-architect` is a Claude Code skill that transforms unstructured brainstorming notes, meeting records, or conversation logs into standardized engineering documentation through a systematic "Thinking Funnel" workflow.

---

## Key Features

- **Structured Transformation:** Converts raw brainstorming into professional documentation
- **Progressive Disclosure:** Three-layer content organization (workflow → rules → templates)
- **Auto-Generated Directories:** Semantic output directories based on input title
- **Node.js Powered:** Coverage analysis uses Node.js (built-in to Claude Code)
- **Long-Tail Capture:** Preserves valuable details that don't fit standard templates
- **Multi-Template Support:** Choose from pre-built templates or provide custom ones
- **Automated Validation:** Built-in scripts run automatically during workflow
- **Merge Support:** Intelligently merges with existing documents

---

## Quick Start

### Installation

The skill is located at:

```
.claude/skills/doc-architect/
```

### Basic Usage

```bash
# In Claude Code CLI
> "Use doc-architect skill to process brainstorm.md and generate engineering docs"
```

The skill will guide you through:
1. Selecting input document (or auto-detecting `*.md` files)
2. Auto-generating output directory from input title
3. Choosing template scheme (A/B/C)
4. Generating documentation
5. Running automated validation scripts
6. Providing execution report with results

---

## Output Structure

```
doc-arch/
└── <core-concept>/                    # Auto-generated from input title
    ├── 00_Key_Points_List.md          # Raw extraction from brainstorm
    ├── 01_Structured_Notes.md         # Categorized extraction (3 dimensions)
    ├── 02_PRD.md                      # Product Requirements (template A)
    ├── 03_System_Architecture.md      # Architecture Design (template A)
    ├── 04_API_Documentation.md        # API Documentation (template A)
    ├── 99_Value_Details.md            # Long-tail valuable details
    └── diff-report.md                 # Optional: Generated if previous version exists
```

### Directory Naming Examples

| Input Title | Generated Directory |
|-------------|---------------------|
| `AI-Powered Task Manager` | `doc-arch/ai-powered-task-manager/` |
| `E-commerce Payment System Design` | `doc-arch/e-commerce-payment-system/` |
| `User Authentication Flow Discussion` | `doc-arch/user-authentication-flow/` |
| `Kura Platform Architecture` | `doc-arch/kura-platform-architecture/` |

**Extraction Rules:**
- Read first `#` heading in document
- Extract 2-5 core words
- Convert to kebab-case (lowercase, hyphens)
- Remove special characters (except hyphens)

---

## Template Schemes

### Option A: General Engineering (Recommended)

| File | Purpose |
|------|---------|
| `02_PRD.md` | Product Requirements Document |
| `03_System_Architecture.md` | System Architecture Design |
| `04_API_Documentation.md` | API Documentation |

### Option B: Simplified Universal

| File | Purpose |
|------|---------|
| `02_Problem_Definition.md` | Problem Definition |
| `03_Solution_Design.md` | Solution Design |
| `04_Action_Plan.md` | Action Plan |

### Option C: Custom Template

Provide your own template directory path.

---

## Workflow (Thinking Funnel)

```
┌─────────────────────────────────────────────────────────────┐
│ P0: User Intent Confirmation                                │
│   → Input file, auto-generate output directory              │
├─────────────────────────────────────────────────────────────┤
│ P1: Template Selection                                     │
│   → Choose A/B/C, load templates                           │
├─────────────────────────────────────────────────────────────┤
│ P2: Raw Capture                                            │
│   → Extract keywords, concepts, decisions, questions       │
│   → Output: 00_Key_Points_List.md                          │
├─────────────────────────────────────────────────────────────┤
│ P3: Core Extraction & Categorization                       │
│   → 3-dimensional classification (Business/Tech/Specs)     │
│   → Output: 01_Structured_Notes.md                         │
├─────────────────────────────────────────────────────────────┤
│ P4: Document Mapping & Generation                          │
│   → Map to templates, merge if exists                      │
│   → Output: 02_*.md, 03_*.md, etc.                         │
├─────────────────────────────────────────────────────────────┤
│ P4.5: Value Detail Capture                                 │
│   → Identify unmapped valuable content                     │
│   → Output: 99_Value_Details.md                           │
├─────────────────────────────────────────────────────────────┤
│ P5-A: Iterative Validation                                 │
│   → Error check, omission check, contradiction check       │
│   → [AUTO] Run validate-intermediate-output.sh             │
├─────────────────────────────────────────────────────────────┤
│ P5-B: Cross-Document Consistency                           │
│   → Concept, process, constraint consistency               │
├─────────────────────────────────────────────────────────────┤
│ P6: Execution Report                                       │
│   → [AUTO] Run check-template-coverage.py (if available)   │
│   → [AUTO] Run diff-report-generator.sh (if old version)  │
│   → Compile final report with script results              │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
doc-architect/
├── SKILL.md                            # Core workflow (~2,000 words)
├── README.md                           # This file
├── prompts/                            # Extraction & mapping rules
│   ├── 1_extraction.md
│   └── 2_mapping.md
├── references/                         # Detailed guidelines
│   ├── value-categorization.md         # Phase 4.5 rules
│   ├── report-format.md                # Phase 6 template
│   └── validation-checklist.md         # Phase 5 checklist
├── templates/                          # Document templates
│   ├── option-a/                       # General Engineering
│   │   ├── 01_PRD.md
│   │   ├── 02_System_Architecture.md
│   │   └── 03_API_Documentation.md
│   └── option-b/                       # Simplified Universal
│       ├── 01_Problem_Definition.md
│       ├── 02_Solution_Design.md
│       └── 03_Action_Plan.md
├── examples/                           # Input/output examples
│   ├── input-example.md
│   └── output-structure.md
└── scripts/                            # Validation tools (auto-run during workflow)
    ├── validate-intermediate-output.sh
    ├── check-template-coverage.js       # Node.js
    └── diff-report-generator.sh
```

---

## Automated Validation Scripts

Scripts run automatically during the workflow:

### P5-A: Intermediate Output Validation

```bash
bash scripts/validate-intermediate-output.sh doc-arch/<core-concept>/
```

**What it checks:**
- Required sections present in `00_Key_Points_List.md`
- Dimensions and subsections present in `01_Structured_Notes.md`
- Table format and value categories in `99_Value_Details.md`

**On failure:** Reports issues, continues workflow (non-blocking)

### P6: Coverage Analysis

```bash
# Run coverage analysis (Node.js)
if command -v node >/dev/null 2>&1; then
    node scripts/check-template-coverage.js doc-arch/<core-concept>/
else
    echo "⚠️  Coverage analysis skipped (Node.js unavailable)"
fi
```

**What it provides:**
- Coverage rate percentage
- Not-covered items list
- Value details summary

**Environment:** Node.js is built-in to Claude Code

### P6: Diff Report Generation

```bash
bash scripts/diff-report-generator.sh doc-arch/<core-concept>.old/ doc-arch/<core-concept>/
```

**What it provides:**
- File statistics comparison
- Detailed diff analysis
- Change summaries

**On no previous version:** Skipped

---

## Manual Script Usage

You can also run scripts manually after generation:

```bash
# Validate intermediate output format
bash scripts/validate-intermediate-output.sh doc-arch/<core-concept>/

# Analyze template coverage (Node.js)
node scripts/check-template-coverage.js doc-arch/<core-concept>/

# Generate diff report (requires previous version)
bash scripts/diff-report-generator.sh doc-arch/<core-concept>.old/ doc-arch/<core-concept>/
```

---

## Value Details Document

The `99_Value_Details.md` file captures valuable content that doesn't fit into standard templates:

| Category | Purpose |
|----------|---------|
| Future Considerations | Ideas for future versions |
| Alternative Approaches | Discarded options worth documenting |
| Implementation Details | Technical nuances not in templates |
| User Insights | User feedback or preferences |
| Edge Cases | Corner cases or special scenarios |
| Dependencies | External factors or relationships |
| Open Questions | Unresolved items needing attention |

---

## Best Practices

### Input Preparation

- Use clear, chronological brainstorming notes
- Include diverse perspectives (technical, business, user)
- Mark decisions and open questions explicitly
- Start with a clear title (first `#` heading)

### Template Selection

- **Option A:** Software projects requiring PRD, architecture, API docs
- **Option B:** General projects needing problem-solution-action structure
- **Option C:** Custom documentation requirements

### Review Process

1. Check `00_Key_Points_List.md` for extraction accuracy
2. Verify `01_Structured_Notes.md` categorization
3. Review `99_Value_Details.md` for important items
4. Check automated validation results in execution report
5. Verify coverage rate (>80% recommended)

---

## Fact Source Rules

During validation (P5-A, P5-B):

```
✓ Use: Original document → 00_Key_Points_List.md → 01_Structured_Notes.md
✗ Never: Generated documents (02_+, 03_+, etc.)
```

This ensures accuracy and prevents circular validation.

---

## Progressive Disclosure

The skill uses three-layer content loading:

1. **Metadata (name + description)** - Always loaded (~100 words)
2. **SKILL.md body** - When skill triggers (~2,000 words)
3. **Bundled resources** - As needed (prompts/, references/, templates/)

This optimizes context usage while providing comprehensive guidance.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.5.3 | 2024-01-17 | Migrate coverage analysis to JavaScript (Node.js) |
| 0.5.2 | 2024-01-17 | Auto-generate semantic output directory from input title |
| 0.5.1 | 2024-01-17 | Add automated script execution to workflow |
| 0.5.0 | 2024-01-17 | Complete restructure with references/, examples/, scripts/ |
| 0.1.0 | - | Initial concept |
| 0.1.0 | - | Initial concept |

---

## Contributing

To extend or modify this skill:

1. **Add templates:** Create new subdirectories in `templates/`
2. **Modify extraction:** Edit `prompts/1_extraction.md`
3. **Update mapping:** Edit `prompts/2_mapping.md`
4. **Add validation rules:** Update `references/validation-checklist.md`
5. **Add scripts:** Place executable scripts in `scripts/`

---

## License

This skill is part of the doc-architect project for Claude Code CLI.

---

## Support

For issues or questions:

1. Check `examples/` for usage patterns
2. Review `references/` for detailed rules
3. Review generated execution report for script results
4. Check `99_Value_Details.md` for missing content
