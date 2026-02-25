# Document Mapping Rules

This document defines the logic for Phase 4 (Document Mapping & Generation) of the doc-architect workflow.

## Mapping Strategy

Map Structured Notes (from Phase 3) to document templates based on semantic alignment and content relevance.

### General Mapping Principles

1. **Semantic Alignment**: Match content meaning to document purpose
2. **Completeness**: Ensure all extracted content is mapped somewhere
3. **Consistency**: Maintain consistent terminology across documents
4. **Traceability**: Keep references to source material

---

## Template Option A: General Engineering Documentation

### 01_PRD.md Mapping

| Template Section | Source from Structured Notes | Notes |
|------------------|------------------------------|-------|
| **Product Vision** | Value Proposition items | Capture the "why" and unique value |
| **Problem Statement** | Pain Points | Describe what problem we're solving |
| **User Personas** | Core Interaction context | Who is using this |
| **User Stories** | Core Interaction items | As a [user], I want [goal], so that [benefit] |
| **Functional Requirements** | All Dimensions | Convert extracted points to requirements |
| **Non-Functional Requirements** | Constraints (Dimension 2) | Performance, security, scalability |
| **Success Metrics** | Value Proposition | Measurable outcomes |

#### Content Expansion Guidelines

**Product Vision:**
- Start with value proposition items
- Expand into a clear, inspiring statement
- Include the long-term vision

**Problem Statement:**
- Compile all pain points
- Organize by severity or frequency
- Include user quotes if available

**Functional Requirements:**
- Map each extracted point to a requirement
- Use format: "The system shall [action]"
- Mark priority: Must/Should/Could

**Non-Functional Requirements:**
- Extract from technical constraints
- Include: performance, security, compatibility, maintainability

---

### 02_System_Architecture.md Mapping

| Template Section | Source from Structured Notes | Notes |
|------------------|------------------------------|-------|
| **High-Level Design** | Key Components + Data Flow | Use Mermaid diagrams |
| **Component Design** | Key Components | Detail each component's role |
| **Data Flow** | Data Flow items | Trace data through the system |
| **Communication Protocols** | Data Flow + Constraints | APIs, events, messaging |
| **Security & Sandbox** | Constraints | Security boundaries |
| **Technology Stack** | Keywords + Components | List technologies chosen |

#### Content Expansion Guidelines

**High-Level Design:**
- Create Mermaid diagram showing component relationships
- Include: components, data flows, external dependencies
- Annotate key interactions

**Component Design:**
- For each key component, document:
  - Purpose and responsibility
  - Interfaces (inputs/outputs)
  - Dependencies on other components

**Data Flow:**
- Sequence diagram for critical paths
- State diagram for stateful components
- Document data formats and transformations

**Communication Protocols:**
- Specify API contracts
- Event schemas
- Message formats

---

### 03_API_Documentation.md Mapping

| Template Section | Source from Structured Notes | Notes |
|------------------|------------------------------|-------|
| **API Overview** | Key Components + Input/Output | High-level API description |
| **Authentication** | Constraints (Dimension 2) | Auth mechanisms |
| **Endpoints** | Input/Output items | Detailed endpoint specs |
| **Data Models** | Input/Output | Request/response schemas |
| **Error Handling** | Error Handling items | Error codes and handling |

#### Content Expansion Guidelines

**API Overview:**
- Describe the API's purpose
- List available endpoints grouped by resource
- Include base URL and versioning strategy

**Endpoints:**
- For each endpoint from Input/Output items:
  - HTTP method and path
  - Request parameters (path, query, body)
  - Response format and status codes
  - Example requests and responses

**Data Models:**
- Schema definitions for all request/response bodies
- Use clear type definitions
- Include validation rules

**Error Handling:**
- Error code reference table
- Error response format
- Recovery strategies

---

## Template Option B: Simplified Universal

### 01_Problem_Definition.md Mapping

| Template Section | Source from Structured Notes | Notes |
|------------------|------------------------------|-------|
| **Problem Summary** | Pain Points | Concise problem description |
| **Current State** | Pain Points | How things work now |
| **Impact** | Pain Points + Value Prop | Why this matters |
| **Root Causes** | Pain Points | Underlying issues |

#### Content Expansion Guidelines

Focus on clarity and brevity. Use:
- Bullet points for quick scanning
- User stories to illustrate problems
- Quantified impact where possible

---

### 02_Solution_Design.md Mapping

| Template Section | Source from Structured Notes | Notes |
|------------------|------------------------------|-------|
| **Solution Overview** | All Dimensions | High-level approach |
| **Key Components** | Key Components | Main building blocks |
| **Data Flow** | Data Flow items | How information moves |
| **Technical Approach** | Constraints + Components | Implementation strategy |
| **Considerations** | All Constraints | Trade-offs and limitations |

#### Content Expansion Guidelines

Balance breadth and depth:
- Provide enough detail for implementation
- Keep sections focused
- Use diagrams for complex relationships

---

### 03_Action_Plan.md Mapping

| Template Section | Source from Structured Notes | Notes |
|------------------|------------------------------|-------|
| **Implementation Phases** | All Dimensions | Logical ordering of work |
| **Milestones** | Value Proposition | Measurable checkpoints |
| **Dependencies** | Question Points | External dependencies |
| **Risks** | Question Points + Constraints | Potential blockers |

#### Content Expansion Guidelines

Create actionable plan:
- Phase 1: Foundation (components, infrastructure)
- Phase 2: Core features (main functionality)
- Phase 3: Enhancement (optimization, polish)
- Include deliverables for each phase

---

## Custom Template Mapping (Option C)

When user provides custom templates:

### Analysis Process

1. **Parse Template Structure**
   - Identify all section headers
   - Recognize placeholder patterns
   - Note template-specific formatting

2. **Infer Section Purpose**
   - Analyze section titles
   - Contextualize with surrounding structure
   - Determine appropriate content type

3. **Create Dynamic Mapping**
   - Match Structured Notes to template sections
   - Use semantic similarity for alignment
   - Flag sections lacking clear mapping

4. **Validate Coverage**
   - Ensure all Structured Notes are mapped
   - Identify template sections without content
   - Prompt user for missing information if needed

### Mapping Heuristics

| Template Keywords | Likely Source |
|-------------------|---------------|
| "Vision", "Overview", "Summary" | Value Proposition |
| "Problem", "Challenge", "Need" | Pain Points |
| "User", "Persona", "Actor" | Core Interaction |
| "Architecture", "Design", "System" | Key Components |
| "API", "Interface", "Contract" | Input/Output |
| "Flow", "Pipeline", "Process" | Data Flow |
| "Security", "Privacy", "Auth" | Constraints |
| "Error", "Exception", "Failure" | Error Handling |

---

## Content Generation Guidelines

### Writing Style

- **Be precise**: Use exact terminology from source
- **Be complete**: Don't omit details for brevity
- **Be consistent**: Use same terms across documents
- **Be actionable**: Write content that guides implementation

### Handling Uncertainty

When source material is ambiguous or incomplete:

1. **Mark explicitly**: Use `[TODO: Verify]` or `[NEEDS CLARIFICATION]` tags
2. **Document assumptions**: State assumptions clearly
3. **Request confirmation**: Flag items for user review

### Cross-References

Create links between related content:
- Use `See also: [Document](section)` for related sections
- Reference specific requirements from other docs
- Maintain bidirectional links where relevant

---

## Merge Strategy (When Documents Exist)

### Diff Analysis

1. **Read existing document**
2. **Compare with new content**
3. **Classify changes:**
   - **Added**: New content not in existing
   - **Modified**: Content that changed
   - **Deleted**: Content removed (rare, confirm with user)
   - **Unchanged**: Content preserved as-is

### Merge Process

```
FOR each section in template:
  IF section exists in target document:
    IF content is semantically different:
      Apply diff and merge
      Preserve non-conflicting content
      Mark conflicts for review
    ELSE:
      Keep existing content
  ELSE:
    Add new section
```

### Merge Output

After merge, document changes:
```
=== MERGE SUMMARY FOR [filename.md] ===
Sections Added: N
Sections Modified: N
Sections Deleted: N
Sections Unchanged: N
```

---

## Validation Before Writing

Before writing any document:

### Completeness Check
- [ ] All Structured Notes mapped to sections
- [ ] All template sections addressed (or marked as N/A)
- [ ] No orphaned content

### Consistency Check
- [ ] Terminology consistent with source
- [ ] No contradictions within document
- [ ] References to other documents are valid

### Quality Check
- [ ] Sections are properly structured
- [ ] Content is actionable
- [ ] Ambiguities are flagged

---

## Transition to Phase 5

After document generation, proceed to Phase 5 (Validation) following the rules in SKILL.md.
