# Validation Checklist

This document provides detailed checklists for Phase 5-A (Iterative Validation) and Phase 5-B (Cross-Document Consistency), ensuring thorough quality assurance of generated documentation.

---

## Phase 5-A: Iterative Validation & Correction

### Goal

Ensure each generated document accurately reflects the original intent from the brainstorming input.

### Fact Source Priority

```
1. ✓ Original brainstorming document (PRIMARY - INPUT_FILE)
2. ✓ 00_Key_Points_List.md (SECONDARY - raw extraction)
3. ✓ 01_Structured_Notes.md (TERTIARY - categorized extraction)
4. ✗ Generated documents (NOT ALLOWED as reference)
```

---

## Iteration 1: Error Check

### Purpose

Identify and correct misinterpretations, factual errors, or distortions.

### Checklist

For each generated document `D`:

| Check | Question | Action if YES |
|-------|----------|---------------|
| **EC-1** | Does the document contain claims not supported by original source? | Remove or mark for verification |
| **EC-2** | Are technical terms used incorrectly compared to source? | Correct terminology |
| **EC-3** | Are user quotes or insights accurately represented? | Correct or mark as paraphrase |
| **EC-4** | Are requirements/features accurately captured? | Verify against source and correct |
| **EC-5** | Are there factual inconsistencies with source? | Correct based on source truth |

### Correction Process

```
For each error found:
├── Identify error in generated document
├── Locate corresponding content in original source
├── Verify correct interpretation
├── Apply correction to generated document
└── Document correction in quality report
```

### Marking Suspicious Content

When uncertain:

```markdown
[TODO: VERIFY] Content that may need verification
[NEEDS CLARIFICATION] Content requiring user input
[CONFIRMED] Content verified against source
```

---

## Iteration 2: Omission Check

### Purpose

Identify and supplement missing key points from the original brainstorming.

### Checklist

For each generated document `D`:

| Check | Question | Action if YES |
|-------|----------|---------------|
| **OC-1** | Are all pain points from source addressed? | Add missing pain points |
| **OC-2** | Are all key decisions documented? | Add missing decisions |
| **OC-3** | Are all user personas represented? | Add missing personas |
| **OC-4** | Are all constraints listed? | Add missing constraints |
| **OC-5** | Are all requirements captured? | Add missing requirements |
| **OC-6** | Are all key components mentioned? | Add missing components |

### Cross-Reference Method

```
For each item in 00_Key_Points_List.md:
├── Search for related content in generated documents
├── If found → Mark as covered
└── If not found → Add to appropriate document or value details
```

### Omission Categories

| Category | Where to Add |
|----------|-------------|
| Missing pain points | PRD → Problem Statement |
| Missing decisions | Architecture → Design Decisions |
| Missing requirements | PRD → Functional Requirements |
| Missing constraints | Architecture → Constraints |
| Missing user insights | 99_Value_Details.md → User Insights |
| Missing alternatives | 99_Value_Details.md → Alternative Approaches |

---

## Iteration 3: Contradiction Check

### Purpose

Identify and resolve internal contradictions within documents and contradictions with the source.

### Checklist

For each generated document `D`:

| Check | Question | Action if YES |
|-------|----------|---------------|
| **CC-1** | Does the document contain internally contradictory statements? | Resolve or mark for discussion |
| **CC-2** | Do requirements conflict with constraints? | Document and flag |
| **CC-3** | Does the document contradict the original source? | Correct to match source |
| **CC-4** | Are there conflicting timelines or priorities? | Resolve conflicts |
| **CC-5** | Do technical approaches contradict each other? | Resolve or present alternatives |

### Contradiction Types

#### Internal Contradictions

```
Example:
  Section A: "System must support offline mode"
  Section B: "System requires constant internet connection"

Resolution: Clarify scope or mark as requirement conflict
```

#### Source Contradictions

```
Example:
  Generated doc: "Users prefer dark mode"
  Source doc: "Users explicitly requested light mode only"

Resolution: Correct generated doc to match source
```

### Resolution Strategy

```
For each contradiction:
├── Identify conflicting statements
├── Check original source for truth
├── Determine correct interpretation
├── Apply correction
└── If truly ambiguous → Add to 99_Value_Details.md → Open Questions
```

---

## Phase 5-B: Cross-Document Consistency Check

### Goal

Ensure consistency across all generated final documents.

### Constraint

```
NEVER use generated documents to cross-reference each other.
ALWAYS use original document and intermediate products as source of truth.
```

### Fact Sources for Cross-Document Checks

```
1. ✓ Original brainstorming document (PRIMARY)
2. ✓ 00_Key_Points_List.md (raw extraction reference)
3. ✓ 01_Structured_Notes.md (categorized extraction reference)
4. ✗ Generated documents (NOT ALLOWED for cross-reference)
```

---

## Check 1: Concept Consistency

### Purpose

Ensure definitions and descriptions of the same concept are consistent across documents.

### Checklist

| Check | Question | Action if NO |
|-------|----------|-------------|
| **CON-1** | Are product terms used consistently? | Standardize terminology |
| **CON-2** | Are component names consistent? | Use consistent naming |
| **CON-3** | Are technical definitions aligned? | Resolve differences |
| **CON-4** | Are user personas consistent? | Standardize descriptions |
| **CON-5** | Are requirement IDs/references consistent? | Align references |

### Verification Process

```
For each concept mentioned in multiple documents:
├── Extract definition from each document
├── Compare against original source
├── Identify discrepancies
├── Determine correct definition from source
└── Apply corrections to all documents
```

### Common Inconsistencies

| Concept | Documents to Check | Common Issue |
|---------|-------------------|--------------|
| Product name | All | Capitalization, spacing |
| Component names | Architecture, API | Naming convention |
| Requirement IDs | PRD, Architecture | ID format, numbering |
| User personas | PRD, UX Flow | Names, descriptions |
| Technical terms | All | Spelling, capitalization |

---

## Check 2: Process Consistency

### Purpose

Ensure workflows, processes, and interactions described across documents align.

### Checklist

| Check | Question | Action if NO |
|-------|----------|-------------|
| **PROC-1** | Do user journeys match across documents? | Align workflows |
| **PROC-2** | Are API endpoints consistent with architecture? | Match endpoints to components |
| **PROC-3** | Do data flows align across documents? | Synchronize flows |
| **PROC-4** | Are interaction sequences consistent? | Align sequences |
| **PROC-5** | Do state transitions match? | Resolve differences |

### Cross-Document Workflow Validation

```
User Journey Flow:
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  PRD        │ ───▶ │  UX Flow    │ ───▶ │ Arch        │
│  (Stories)  │      │  (Sequence) │      │  (Flow)     │
└─────────────┘      └─────────────┘      └─────────────┘
       │                    │                    │
       └────────────────────┴────────────────────┘
                    Verify alignment
```

### Validation Matrix

| Workflow | PRD | UX Flow | Architecture | API Docs |
|----------|-----|---------|--------------|----------|
| User login | ✓ | ✓ | ✓ | ✓ |
| Data submission | ✓ | ✓ | ✓ | ✓ |
| Error handling | ✓ | ✓ | ✓ | ✓ |

---

## Check 3: Constraint Consistency

### Purpose

Ensure technical, business, and regulatory constraints are consistently represented.

### Checklist

| Check | Question | Action if NO |
|-------|----------|-------------|
| **CONSTR-1** | Are performance targets consistent? | Align metrics |
| **CONSTR-2** | Are security requirements aligned? | Match security specs |
| **CONSTR-3** | Are compliance requirements consistent? | Standardize requirements |
| **CONSTR-4** | Are technical constraints documented in all relevant docs? | Add missing constraints |
| **CONSTR-5** | Are business constraints consistent? | Align constraints |

### Constraint Categories

| Category | Documents | Check Items |
|----------|-----------|-------------|
| Performance | PRD, Architecture | Response time, throughput |
| Security | All | Auth, encryption, compliance |
| Scalability | PRD, Architecture | User limits, growth |
| Compatibility | PRD, API Docs | Platforms, versions |
| Regulatory | PRD, Architecture | GDPR, HIPAA, etc. |

---

## Conflict Resolution Process

### When Conflicts Are Found

```
┌─────────────────────────────────────────────────────────┐
│ 1. Identify Conflict                                    │
│    → Which documents? Which sections?                   │
├─────────────────────────────────────────────────────────┤
│ 2. Return to Source Documents                           │
│    → Check original brainstorming                       │
│    → Check 00_Key_Points_List.md                        │
│    → Check 01_Structured_Notes.md                       │
├─────────────────────────────────────────────────────────┤
│ 3. Determine Truth                                      │
│    → What is the correct information?                   │
│    → Is there ambiguity in source?                      │
├─────────────────────────────────────────────────────────┤
│ 4. Apply Resolution                                     │
│    → Correct all affected documents                     │
│    → OR mark as open question if ambiguous              │
├─────────────────────────────────────────────────────────┤
│ 5. Document Resolution                                  │
│    → Log in quality report                              │
│    → Add to 99_Value_Details.md if needed              │
└─────────────────────────────────────────────────────────┘
```

### Resolution Outcomes

| Outcome | Action | Documentation |
|----------|--------|---------------|
| Clear correction | Update all documents | Quality report |
| Source ambiguity | Add to Open Questions | 99_Value_Details.md |
| Intentional difference | Document rationale | Affected documents |
| Requires user input | Mark for review | Action items |

---

## Quality Metrics

### Target Metrics

| Metric | Target | Acceptable |
|--------|--------|------------|
| Error corrections | < 5 per document | < 10 |
| Omissions per document | < 3 | < 5 |
| Contradictions | 0 | < 2 |
| Cross-document conflicts | 0 | < 3 |
| Concept inconsistencies | 0 | < 2 |

### Warning Thresholds

Trigger review when:

- Errors corrected > 10 per document
- Omissions > 5 per document
- Contradictions > 2
- Cross-document conflicts > 3
- Concept inconsistencies > 2

---

## Validation Log Template

```markdown
## Validation Log for [Document Name]

### Iteration 1: Error Check
- EC-1: [Error found/corrected]
- EC-2: [Error found/corrected]
...
Errors corrected: N

### Iteration 2: Omission Check
- OC-1: [Omission found/supplemented]
- OC-2: [Omission found/supplemented]
...
Omissions supplemented: N

### Iteration 3: Contradiction Check
- CC-1: [Contradiction found/resolved]
- CC-2: [Contradiction found/resolved]
...
Contradictions resolved: N

### Cross-Document Checks
- Concept consistency: [Status]
- Process consistency: [Status]
- Constraint consistency: [Status]
```

---

## Best Practices

### DO:
✅ Always verify against original source first
✅ Use intermediate products (00_, 01_) for reference
✅ Document all corrections made
✅ Add truly ambiguous items to Open Questions
✅ Be thorough - catch issues early

### DON'T:
❌ Don't use generated docs as reference for validation
❌ Don't ignore ambiguities - flag them
❌ Don't make assumptions beyond source content
❌ Don't skip validation steps
❌ Don't correct without verification

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.5.0 | [DATE] | Initial validation checklist for doc-architect skill |
