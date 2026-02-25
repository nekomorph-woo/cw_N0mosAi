# Output Structure Example

This document illustrates the expected output structure when using the doc-architect skill with the example brainstorming input.

---

## Phase 0: Auto-Generated Output Directory

Based on the input document title **"AI-Powered Task Manager"**, the skill auto-generates:

```
doc-arch/ai-powered-task-manager/
```

**Extraction Logic:**
1. Read first heading: `# AI-Powered Task Manager`
2. Extract core concept: "AI-Powered Task Manager"
3. Convert to kebab-case: `ai-powered-task-manager`
4. Create directory: `doc-arch/ai-powered-task-manager/`

---

## Directory Structure

```
doc-arch/
└── ai-powered-task-manager/              # Auto-generated from input title
    ├── 00_Key_Points_List.md            # Intermediate: Raw extraction
    ├── 01_Structured_Notes.md           # Intermediate: Categorized extraction
    ├── 02_PRD.md                        # Final: Product Requirements
    ├── 03_System_Architecture.md        # Final: Architecture Design
    ├── 04_API_Documentation.md          # Final: API Documentation
    ├── 99_Value_Details.md              # Value details (long-tail content)
    └── diff-report.md                   # Optional: Generated if doc-arch.old exists
```

---

## File Content Summaries

### 00_Key_Points_List.md

**Purpose:** Raw extraction of all key points from brainstorming

**Location:** `doc-arch/ai-powered-task-manager/00_Key_Points_List.md`

**Content Structure:**

```markdown
# Key Points List

## Keywords
- Task manager
- Natural language
- Proactive suggestions
- Local-first
- Privacy
- AI-powered
- Learning system

## New Concepts
- **Conversational task capture**: Chat-based input
- **Proactive intelligence**: AI suggests tasks before user asks
- **Adaptive scheduling**: Learns user productivity patterns
- **Privacy-first architecture**: Local storage with optional sync

## Decision Points
- **Mobile-first strategy**: Start with mobile, web later
- **Local-first data**: SQLite local, Firebase for sync
- **3-month MVP timeline**: Scope accordingly
- **Must-haves vs nice-to-haves**: NLP capture, scheduling, local storage (must)

## Question Points
- How to handle recurring tasks?
- Subtasks support?
- Pricing model?
- User accounts required?
- Multi-language support?
```

---

### 01_Structured_Notes.md

**Purpose:** Three-dimensional categorization of extracted content

**Location:** `doc-arch/ai-powered-task-manager/01_Structured_Notes.md`

**Content Structure:**

```markdown
# Structured Notes

## [Dimension 1] Business / Value

### Pain Points
- [P1] Current task managers too complex, high onboarding friction
- [P2] Users spend more time managing than doing
- [P3] Poor natural language understanding in competitors

### Core Interaction
- [I1] Natural language input: "buy milk tomorrow" → AI figures out context
- [I2] Conversational interface: Chat-like experience
- [I3] Proactive suggestions: AI suggests tasks based on patterns
- [I4] Confirmation-based: AI suggests, user confirms

### Value Proposition
- [V1] 10x faster onboarding (no tutorial needed)
- [V2] Natural language-first (no forms)
- [V3] Proactive intelligence (suggests, doesn't just record)
- [V4] Privacy-focused (local-first, optional cloud)

## [Dimension 2] Technical / Architecture

### Data Flow
- User input → NLP processing → Task extraction → Local storage
- Pattern learning → Task suggestions → User confirmation
- Optional: Cloud sync via Firebase

### Key Components
- Mobile app (React Native)
- Local database (SQLite with encryption)
- NLP service (OpenAI API)
- Sync service (Firebase - optional)
- Pattern learning engine

### Constraints
- Privacy-first: Data stays on device by default
- MVP timeline: 3 months
- API costs: Batch calls, cache responses
- Platform: Mobile-first (iOS/Android via React Native)

## [Dimension 3] Specs / Constraints

### Input/Output
- Input: Natural language text or voice
- Output: Structured task with time, priority, context
- API: OpenAI API for NLP processing

### Directory Structure
- React Native project structure
- Local database encryption layer
- API abstraction for cloud services

### Error Handling
- Ambiguous input: Ask clarifying questions
- API failures: Fall back to basic parsing
- Offline mode: Queue sync for later
```

---

### 02_PRD.md

**Purpose:** Product Requirements Document

**Location:** `doc-arch/ai-powered-task-manager/02_PRD.md`

**Key Sections Populated:**

| Section | Source Content |
|---------|----------------|
| Product Vision | AI-powered task manager that learns and suggests |
| Problem Statement | Current apps too complex, high friction |
| User Stories | "As a busy parent, I want to quickly capture tasks..." |
| Functional Requirements | NLP input, smart scheduling, local storage |
| Non-Functional Requirements | Privacy, performance, 3-month MVP |

---

### 03_System_Architecture.md

**Purpose:** System Architecture Design

**Location:** `doc-arch/ai-powered-task-manager/03_System_Architecture.md`

**Key Sections Populated:**

| Section | Source Content |
|---------|----------------|
| High-Level Design | Mobile → NLP → Local DB + Optional Cloud |
| Component Design | React Native app, SQLite, OpenAI API, Firebase |
| Data Flow | Input → NLP → Task → Storage → Suggestions |
| Security | Encryption, local-first, optional sync |

---

### 04_API_Documentation.md

**Purpose:** API Documentation

**Location:** `doc-arch/ai-powered-task-manager/04_API_Documentation.md`

**Key Sections Populated:**

| Section | Source Content |
|---------|----------------|
| API Overview | Task CRUD, Suggestions, Sync |
| Authentication | Local auth, optional cloud account |
| Endpoints | POST /tasks (natural language), GET /suggestions |
| Data Models | Task model with NLP-extracted metadata |

---

### 99_Value_Details.md

**Purpose:** Valuable details not fitting into standard templates

**Location:** `doc-arch/ai-powered-task-manager/99_Value_Details.md`

**Content Structure:**

```markdown
# Value Details Outside Template Scope

## Generation Context
- Input File: brainstorm-ai-task-manager.md
- Template Scheme: A (General Engineering)
- Generated On: 2024-01-15

---

## Future Considerations

| Idea | Description | Potential Value |
|------|-------------|-----------------|
| Web version | Desktop browser interface | Power users, productivity |
| Team features | Shared tasks, collaboration | Market expansion |
| Smart watch | Wearable integration | Quick capture convenience |
| Calendar sync | Two-way calendar integration | Ecosystem integration |

*Count: 4 items*

---

## Alternative Approaches

| Approach | Why Discarded | When to Reconsider |
|----------|---------------|-------------------|
| Calendar integration (MVP) | Too complex for 3-month timeline | Post-MVP, if user demand high |
| Social features | Not core value, adds complexity | For team-focused version |
| Templates system | Competitors do this, differentiate with AI | If AI isn't sufficient differentiator |

*Count: 3 items*

---

## Implementation Details

| Detail | Context | Reference |
|--------|---------|-----------|
| Batch API calls | Reduce OpenAI API costs | [Source: Input, Line 45] |
| Cache AI responses | Local performance | [Source: Input, Line 46] |
| SQLite encryption | Privacy requirement | [Source: Input, Line 38] |
| Index tasks | Fast search capability | [Source: Input, Line 47] |

*Count: 4 items*

---

## User Insights

| Insight | Source | Implication |
|---------|--------|-------------|
| "Users hate project vs task distinction" | Bob (PM) | Simplify data model |
| "Power users want keyboard shortcuts" | Alice (Designer) | Add to post-MVP roadmap |
| "Most users just want scheduling guidance" | Charlie (Tech) | Prioritize AI scheduling over manual controls |

*Count: 3 items*

---

## Edge Cases

| Case | Description | Handling Consideration |
|------|-------------|------------------------|
| Ambiguous pronouns | "Call him" - who is him? | Ask clarifying question |
| Multi-language input | User switches languages | Detect language, use appropriate model |
| Offline mode | No internet, need NLP | Queue for processing when online, use basic parsing |
| Task override | User rejects AI suggestion | Learn from rejection, update model |

*Count: 4 items*

---

## Dependencies

| Dependency | Type | Impact |
|-------------|------|--------|
| OpenAI API | External API | Cost, rate limits, uptime |
| App Store approval | Regulatory | Timeline risk, review process |
| GDPR/CCPA compliance | Legal | Privacy implementation requirements |

*Count: 3 items*

---

## Open Questions

| Question | Priority | Suggested Resolution |
|----------|----------|----------------------|
| How to handle recurring tasks? | P1 | Research pattern recognition options |
| Should we support subtasks? | P2 | User survey to determine demand |
| What's the pricing model? | P1 | Research competitor pricing, determine value metric |
| User accounts required? | P1 | Evaluate anonymous vs authenticated experience |

*Count: 4 items*

---

## Summary Statistics

- Total Value Items: 25
- Items Requiring Follow-up: 7 (Open Questions + Dependencies)
- High-Priority Items: 3 (P1 Questions)
```

---

## Automated Validation (P5-A)

After manual validation, the skill automatically runs:

```bash
bash scripts/validate-intermediate-output.sh doc-arch/ai-powered-task-manager/
```

**Expected Output:**

```
════════════════════════════════════════════════════════════════
         DOC-ARCHITECT INTERMEDIATE OUTPUT VALIDATOR
════════════════════════════════════════════════════════════════

Checking: 00_Key_Points_List.md
  ✓ Section 'Keywords' found
  ✓ Section 'New Concepts' found
  ✓ Section 'Decision Points' found
  ✓ Section 'Question Points' found
  ✓ All required sections present

Checking: 01_Structured_Notes.md
  ✓ Dimension 'Business / Value' found
  ✓ Dimension 'Technical / Architecture' found
  ✓ Dimension 'Specs / Constraints' found
  ✓ All required dimensions present

Checking: 99_Value_Details.md
  ✓ Generation Context found
  ✓ Table format detected
  ✓ Value categories present

════════════════════════════════════════════════════════════════
                         VALIDATION SUMMARY
════════════════════════════════════════════════════════════════
Total Checks:  3
Passed:       3
Failed:       0

✓ All validations passed!
```

---

## Coverage Analysis (P6)

The skill automatically runs coverage analysis:

```bash
# Run coverage analysis (Node.js)
if command -v node >/dev/null 2>&1; then
    node scripts/check-template-coverage.js doc-arch/ai-powered-task-manager/
else
    echo "⚠️  Coverage analysis skipped (Node.js unavailable)"
fi
```

**Expected Output:**

```
DOC-ARCHITECT TEMPLATE COVERAGE ANALYZER

Analyzing directory: doc-arch/ai-powered-task-manager

COVERAGE SUMMARY
Total Items Analyzed:  25
Covered in Docs:       22
Not Covered:            3
Coverage Rate:         88.0%

⚠ Good coverage, room for improvement

VALUE DETAILS CAPTURE
Total Value Items: 25
  Future Considerations: 4
  Alternative Approaches: 3
  Implementation Details: 4
  User Insights: 3
  Edge Cases: 4
  Dependencies: 3
  Open Questions: 4
```

---

## Expected File Sizes

| File | Approximate Size | Content Type |
|------|-----------------|--------------|
| `00_Key_Points_List.md` | ~500 words | Structured list |
| `01_Structured_Notes.md` | ~1,000 words | Categorized extraction |
| `02_PRD.md` | ~2,000 words | Full PRD template |
| `03_System_Architecture.md` | ~1,500 words | Architecture doc |
| `04_API_Documentation.md` | ~1,200 words | API spec |
| `99_Value_Details.md` | ~800 words | Tabular value details |

**Total:** ~7,000 words across 6 files

---

## Validation Points

After generation, verify:

- [ ] Output directory created: `doc-arch/ai-powered-task-manager/`
- [ ] All pain points from input appear in PRD
- [ ] All technical components in architecture
- [ ] Value details contain items not in other documents
- [ ] No duplication between 99_ and other files
- [ ] All open questions captured
- [ ] Source references present in 99_ file
- [ ] Automated validation passed (P5-A)
- [ ] Coverage analysis acceptable (>80%)

---

## Usage Notes

### Step-by-Step Process

1. **Input:** Start with raw brainstorming notes (like `input-example.md`)
2. **Auto-Directory:** Skill generates `doc-arch/<core-concept>/` from title
3. **Template Selection:** Choose A (General Engineering) for software projects
4. **Generation:** Skill creates all intermediate and final documents
5. **Auto-Validation:** Skill runs validation scripts automatically
6. **Review:** Check intermediate files (00_, 01_) for accuracy
7. **Value Details:** Review 99_ file for important long-tail content
8. **Iterate:** Use Open Questions to guide next discussion

### Running Manual Validation

If you want to manually re-run validation:

```bash
# Validate intermediate output format
bash scripts/validate-intermediate-output.sh doc-arch/ai-powered-task-manager/

# Analyze template coverage (Node.js)
node scripts/check-template-coverage.js doc-arch/ai-powered-task-manager/

# Generate diff report (if previous version exists)
bash scripts/diff-report-generator.sh doc-arch/ai-powered-task-manager.old/ doc-arch/ai-powered-task-manager/
```

---

## Naming Convention Examples

| Input Title | Generated Directory |
|-------------|---------------------|
| `AI-Powered Task Manager` | `doc-arch/ai-powered-task-manager/` |
| `E-commerce Payment System Design` | `doc-arch/e-commerce-payment-system/` |
| `User Authentication Flow Discussion` | `doc-arch/user-authentication-flow/` |
| `Kura Platform Architecture` | `doc-arch/kura-platform-architecture/` |
| `Mobile App Onboarding Improvement` | `doc-arch/mobile-app-onboarding/` |

**Extraction Rules:**
- Read first `#` heading in document
- Extract 2-5 core words
- Convert to lowercase
- Replace spaces with hyphens
- Remove special characters (except hyphens)

---

*This example demonstrates the expected output structure and content organization when using the doc-architect skill (version 0.5.3+).*
