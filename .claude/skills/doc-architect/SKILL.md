---
name: doc-architect
description: This skill should be used when the user asks to "convert brainstorming to engineering docs", "organize ideas into specs", or mentions "transform unstructured notes" to PRD/architecture/API documentation. Follows a systematic "Thinking Funnel" workflow for document generation.
version: 0.5.3
---

# Doc Architect - Document Standard Operating Procedure

Transforms unstructured brainstorming notes into standardized engineering documentation through a systematic "Thinking Funnel" workflow.

---

## Core Workflow

Execute phases P0-P6 in order. For detailed rules, see `references/` directory.

---

### Phase 0: User Intent Confirmation

1. **Confirm Input Source**
   - Ask user to provide the path to the brainstorming document
   - OR detect `*.md` files in current directory and present selection
   - Accept formats: Markdown (`.md`), Text (`.txt`)

2. **Generate Output Directory** (if not specified by user)
   - Read input document title or first heading
   - Extract core concept/summary (2-5 words)
   - Convert to kebab-case (lowercase, hyphens for spaces)
   - Format: `doc-arch/<core-concept>/`

   **Example:**
   - Input: "AI-Powered Task Manager Brainstorming"
   - Output: `doc-arch/ai-powered-task-manager/`

3. **Confirm Output Directory**
   - Auto-generated: `doc-arch/<core-concept>/`
   - Allow user to override with custom path

**Output:** Validated input file path and output directory path

---

### Phase 1: Template Selection

Present options and load templates:

```
[A] General Engineering - 01_PRD.md, 02_System_Architecture.md, 03_API_Documentation.md
[B] Simplified Universal - 01_Problem_Definition.md, 02_Solution_Design.md, 03_Action_Plan.md
[C] Custom Template Path - User provides directory
```

---

### Phase 2: Raw Capture

Read input document → Extract using `prompts/1_extraction.md` → Output `00_Key_Points_List.md`

**Output:** Keywords, new concepts, decision points, question points

---

### Phase 3: Core Extraction & Categorization

Apply three-dimensional classification:

```
[Dimension 1] Business/Value → Pain Points, Core Interaction, Value Proposition
[Dimension 2] Technical/Architecture → Data Flow, Key Components, Constraints
[Dimension 3] Specs/Constraints → Input/Output, Directory Structure, Error Handling
```

**Output:** `01_Structured_Notes.md`

---

### Phase 4: Document Mapping & Generation

For each template file: Load skeleton → Apply `prompts/2_mapping.md` → Merge with existing (if any) → Write file

**Output:** Final documents (`02_*.md`, `03_*.md`, etc.)

---

### Phase 4.5: Value Detail Capture

**Identify unmapped content** → Assess value → Categorize → Output `99_Value_Details.md`

**Categories:** Future Considerations, Alternative Approaches, Implementation Details, User Insights, Edge Cases, Dependencies, Open Questions

**Reference:** `references/value-categorization.md` for detailed rules

**Output:** `99_Value_Details.md` (mandatory for all template schemes)

---

### Phase 5-A: Iterative Validation

For each generated document, execute three iterations against source:

```
Iteration 1: Error Check → Compare with original → Correct misinterpretations
Iteration 2: Omission Check → Find missing key points → Supplement content
Iteration 3: Contradiction Check → Resolve internal/external conflicts
```

**Fact Sources:** Original doc → `00_Key_Points_List.md` → `01_Structured_Notes.md` (NOT generated docs)

**Reference:** `references/validation-checklist.md` for detailed checklist

---

### Automated Validation (Post-P5A)

After manual validation iterations, run automated script validation:

```bash
bash scripts/validate-intermediate-output.sh doc-arch/<core-concept>/
```

**On Success:** Continue to Phase 5-B
**On Failure:** Report issues in execution report, continue workflow (non-blocking)

---

### Phase 5-B: Cross-Document Consistency

Never use generated docs for cross-reference. Always use original + intermediate products.

```
Check 1: Concept Consistency → Verify terms/definitions align
Check 2: Process Consistency → Verify workflows align
Check 3: Constraint Consistency → Verify constraints align
```

**Reference:** `references/validation-checklist.md`

---

### Phase 6: Execution Report

Generate comprehensive report with file creation summary, diff summary, quality metrics, and action items.

**Step 1: Run Coverage Analysis**

```bash
# Run coverage analysis (Node.js)
if command -v node >/dev/null 2>&1; then
    node scripts/check-template-coverage.js doc-arch/<core-concept>/
else
    echo "⚠️  Coverage analysis skipped (Node.js unavailable)"
fi
```

Capture output for inclusion in report.

**Step 2: Generate Diff Report** (if previous version exists)

```bash
# Check for old directory, generate diff if found
if [ -d "doc-arch/<core-concept>.old" ]; then
    bash scripts/diff-report-generator.sh doc-arch/<core-concept>.old/ doc-arch/<core-concept>/ doc-arch/<core-concept>/diff-report.md
fi
```

**Step 3: Compile Final Report**

Include:
- File creation summary
- Script validation results
- Coverage analysis (if available)
- Diff summary (if applicable)
- Quality metrics
- Action items

**Reference:** `references/report-format.md` for template

---

## Output File Structure

```
doc-arch/
└── <core-concept>/                    # Auto-generated from input title
    ├── 00_Key_Points_List.md          # Intermediate: Raw extraction
    ├── 01_Structured_Notes.md         # Intermediate: Categorized extraction
    ├── 02_PRD.md                      # Final: Product Requirements
    ├── 03_System_Architecture.md      # Final: Architecture Design
    ├── 04_API_Documentation.md        # Final: API Documentation
    └── 99_Value_Details.md            # Long-tail valuable details
```

**Example:**
```
doc-arch/
└── ai-powered-task-manager/
    ├── 00_Key_Points_List.md
    ├── 01_Structured_Notes.md
    ├── 02_PRD.md
    ├── 03_System_Architecture.md
    ├── 04_API_Documentation.md
    └── 99_Value_Details.md
```

---

## Fact Source Rules

| Phase | Fact Sources | NOT Allowed |
|-------|--------------|-------------|
| **P5-A** | Original → 00_ → 01_ | ❌ Generated docs |
| **P5-B** | Original → 00_ → 01_ | ❌ Generated docs |

---

## Merge Strategy

| Strategy | Behavior |
|----------|----------|
| **Diff** | Identify added/modified/deleted sections |
| **Merge** | Merge differences into existing document |
| **Preserve** | Keep non-conflicting parts unchanged |

---

## Progressive Disclosure

| Resource | Purpose |
|----------|---------|
| **SKILL.md** (this file) | Core workflow (~2,000 words) |
| **prompts/1_extraction.md** | Extraction and categorization logic |
| **prompts/2_mapping.md** | Document mapping rules |
| **references/value-categorization.md** | Phase 4.5 detailed rules |
| **references/report-format.md** | Phase 6 report template |
| **references/validation-checklist.md** | Phase 5 detailed checklist |
| **templates/** | Actual document templates |
| **examples/** | Input/output examples |
| **scripts/** | Validation and analysis tools |

---

## Validation Scripts

Use scripts in `scripts/` directory:

- **validate-intermediate-output.sh** - Validate 00_ and 01_ file formats
- **check-template-coverage.js** - Analyze mapping coverage (Node.js)
- **diff-report-generator.sh** - Generate diff reports

---

## Usage Example

```bash
# Trigger the skill
> "Use doc-architect skill to process brainstorm.md and generate engineering docs"
```

The skill will:
1. Ask for input file path (or detect markdown files)
2. Present template options (A/B/C)
3. Execute Thinking Funnel workflow (P0-P6)
4. Generate intermediate products (00_, 01_)
5. Generate final documents (02_+, 03_+, 04_+)
6. Generate value details (99_)
7. **Run automated validation scripts** (non-blocking)
8. Provide execution report with diff summary and script results

---

## Writing Style

- Use **imperative/infinitive form** (verb-first instructions)
- Avoid second person ("You should...")
- Be objective and instructional

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.5.3 | 2024-01-17 | Migrate coverage analysis to JavaScript (Node.js) |
| 0.5.2 | 2024-01-17 | Auto-generate semantic output directory from input title |
| 0.5.1 | 2024-01-17 | Add automated script execution to workflow |
| 0.5.0 | 2024-01-17 | Complete restructure with references/, examples/, scripts/ |
