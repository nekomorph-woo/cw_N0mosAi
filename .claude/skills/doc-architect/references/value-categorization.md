# Value Categorization Rules

This document provides detailed guidance for Phase 4.5 (Value Detail Capture), defining how to identify, assess, and categorize valuable content that doesn't fit into template structures.

---

## Purpose

Capture "long-tail" valuable details from brainstorming sessions that would otherwise be lost due to template constraints. This ensures important insights, alternatives, and context are preserved for future reference.

---

## Identification Criteria

### What to Capture

Content should be captured when it meets **at least two** of these criteria:

| Criterion | Description | Examples |
|-----------|-------------|----------|
| **Relevance** | Could be useful in future iterations | "Maybe consider for v2.0", "Alternative approach worth exploring" |
| **Uniqueness** | Unique insight or perspective not commonly found | "Non-obvious solution to X", "Counterintuitive user behavior" |
| **Implementability** | Could become a feature/requirement later | "Technical feasibility note", "Performance optimization opportunity" |
| **Context Value** | Provides important background or rationale | "Why we chose X over Y", "Historical context for decision" |

### What NOT to Capture

- ❌ Duplicate content already in final documents
- ❌ Completely irrelevant or off-topic notes
- ❌ Outdated/superseded decisions (unless historically significant)
- ❌ Trivial or obvious statements

---

## Category Definitions

### 1. Future Considerations

**Definition:** Ideas, features, or improvements that are explicitly deferred to future versions.

| Field | Description | Example |
|-------|-------------|---------|
| Idea | The deferred concept | "Dark mode support" |
| Description | Brief explanation | "Users requested dark theme for night usage" |
| Potential Value | Why this matters | "Accessibility improvement, user satisfaction" |

**When to use:**
- "Nice to have but out of scope"
- "Phase 2 feature"
- "Future enhancement"

---

### 2. Alternative Approaches

**Definition:** Options that were considered but not selected, with rationale and reconsideration conditions.

| Field | Description | Example |
|-------|-------------|---------|
| Approach | The alternative option | "Use SQLite instead of PostgreSQL" |
| Why Discarded | Reason for rejection | "Scalability concerns beyond 10K users" |
| When to Reconsider | Conditions for revisiting | "If user base stays under 10K for 1+ years" |

**When to use:**
- "We considered X but went with Y because..."
- "Discarded option that might be valid later"
- "Technical trade-off decision"

---

### 3. Implementation Details

**Definition:** Technical nuances, specifics, or details that don't fit into standard documentation sections.

| Field | Description | Example |
|-------|-------------|---------|
| Detail | The technical nuance | "Use connection pooling with max 10 connections" |
| Context | Where this applies | "Database layer for high-traffic endpoints" |
| Reference | Source in original document | "[Source: Original Doc, Line 123]" |

**When to use:**
- Specific technical constraints
- Implementation notes
- Configuration specifics
- Performance considerations

---

### 4. User Insights

**Definition:** Feedback, preferences, or behavioral observations from users or stakeholders.

| Field | Description | Example |
|-------|-------------|---------|
| Insight | The user observation | "Users prefer one-click over multi-step" |
| Source | Who provided this | "User interview #3, Product Manager feedback" |
| Implication | What this means | "Simplify UX flow, reduce friction" |

**When to use:**
- User feedback or quotes
- Stakeholder preferences
- Usability findings
- Behavioral patterns

---

### 5. Edge Cases

**Definition:** Corner cases, special scenarios, or exceptional conditions that may need handling.

| Field | Description | Example |
|-------|-------------|---------|
| Case | The edge case scenario | "Concurrent file access by multiple users" |
| Description | What happens | "Race condition potential" |
| Handling Consideration | How to address | "Implement file locking or queue system" |

**When to use:**
- "What if X happens?"
- Rare but important scenarios
- Error conditions
- Boundary cases

---

### 6. Dependencies

**Definition:** External factors, systems, or relationships that impact the project.

| Field | Description | Example |
|-------|-------------|---------|
| Dependency | The external item | "Third-party payment API" |
| Type | Category | External API, Team, Technology, Regulatory |
| Impact | How it affects project | "Requires PCI compliance, affects timeline" |

**When to use:**
- External API dependencies
- Team/resource dependencies
- Technology constraints
- Regulatory requirements

---

### 7. Open Questions

**Definition:** Unresolved items, decisions needed, or clarifications required.

| Field | Description | Example |
|-------|-------------|---------|
| Question | What needs resolution | "Should we support offline mode?" |
| Priority | Urgency level | P0 (Critical), P1 (High), P2 (Medium), P3 (Low) |
| Suggested Resolution | Potential approach | "Research local storage options, present to stakeholders" |

**When to use:**
- Unanswered questions from brainstorming
- Decisions pending
- Clarifications needed
- Research items

---

## Assessment Workflow

```
┌─────────────────────────────────────────┐
│ For each item in Structured Notes:      │
├─────────────────────────────────────────┤
│ 1. Is it in final documents?            │
│    YES → Skip (already captured)        │
│    NO  → Continue to step 2             │
├─────────────────────────────────────────┤
│ 2. Does it meet 2+ criteria?            │
│    NO  → Skip (not valuable enough)     │
│    YES → Continue to step 3             │
├─────────────────────────────────────────┤
│ 3. Which category fits best?            │
│    → Select most appropriate category   │
├─────────────────────────────────────────┤
│ 4. Extract details for table fields     │
│    → Fill in all required fields        │
├─────────────────────────────────────────┤
│ 5. Add source reference                 │
│    → [Source: Document Name, Line #]    │
└─────────────────────────────────────────┘
```

---

## Cross-Reference Validation

Before finalizing the value details document:

### Duplication Check
```bash
# For each item in value details:
1. Search for key terms in all final documents
2. If found with similar meaning → Remove from value details
3. If not found → Keep in value details
```

### Accuracy Check
```bash
# For each item:
1. Verify against original source document
2. Ensure accurate representation
3. Confirm source reference is correct
```

### Categorization Review
```bash
# For each category:
1. Ensure all items fit category definition
2. Move misplaced items to correct categories
3. Consolidate similar items where appropriate
```

---

## Output Format Template

```markdown
# Value Details Outside Template Scope

This document captures valuable details from the original brainstorming that did not fit into the standardized template structure but may be important for future reference or iteration.

## Generation Context
- **Input File:** [INPUT_FILE]
- **Template Scheme:** [A/B/C]
- **Generated On:** [DATE]
- **Total Items Captured:** [N]

---

## Future Considerations

| Idea | Description | Potential Value |
|------|-------------|-----------------|
| [Idea] | [Detail] | [Why valuable] |

*Count: N items*

---

## Alternative Approaches

| Approach | Why Discarded | When to Reconsider |
|----------|---------------|-------------------|
| [Approach] | [Reason] | [Condition] |

*Count: N items*

---

## Implementation Details

| Detail | Context | Reference |
|--------|---------|-----------|
| [Detail] | [Context] | [Source: Doc, Line] |

*Count: N items*

---

## User Insights

| Insight | Source | Implication |
|---------|--------|-------------|
| [Insight] | [Who/Where] | [What it means] |

*Count: N items*

---

## Edge Cases

| Case | Description | Handling Consideration |
|------|-------------|------------------------|
| [Case] | [What happens] | [How to address] |

*Count: N items*

---

## Dependencies

| Dependency | Type | Impact |
|-------------|------|--------|
| [Dependency] | [Category] | [Effect] |

*Count: N items*

---

## Open Questions

| Question | Priority | Suggested Resolution |
|----------|----------|----------------------|
| [Question] | [P0/P1/P2/P3] | [Approach] |

*Count: N items*

---

## Summary Statistics

- **Total Value Items:** [N]
- **Items Requiring Follow-up:** [N] (Open Questions + Dependencies)
- **High-Priority Items:** [N] (P0 + P1 Open Questions)

## Next Actions

1. [ ] Review Open Questions with stakeholders
2. [ ] Assess Dependencies for blocking items
3. [ ] Evaluate Future Considerations for roadmap
```

---

## Best Practices

### DO:
✅ Be specific and concise in descriptions
✅ Always include source references
✅ Use consistent terminology with final documents
✅ Update this document if final documents change
✅ Review periodically during project lifecycle

### DON'T:
❌ Don't duplicate content from final documents
❌ Don't include trivial or obvious statements
❌ Don't mix categories (one item = one category)
❌ Don't include outdated/superseded items
❌ Don't leave fields blank (use "N/A" if truly not applicable)

---

## Maintenance

### When to Update This Document

- After major brainstorming sessions
- When project scope changes significantly
- When new alternatives are considered
- When open questions are resolved

### Version Control

Track changes to this document alongside the main project documentation. Consider it a living document that evolves with the project.
