# Extraction Rules

This document defines the logic for Phase 2 (Raw Capture) and Phase 3 (Core Extraction & Categorization) of the doc-architect workflow.

## Phase 2: Raw Capture (Fragment Collection)

### Goal

Extract all meaningful fragments from the brainstorming document without filtering or judgment.

### Extraction Categories

Capture the following types of content from the input document:

#### 1. Keywords
- Technical terms mentioned repeatedly
- Domain-specific vocabulary
- Product/feature names
- Technology stack references

#### 2. New Concepts
- Ideas introduced during discussion
- Novel approaches or methods
- Innovative solutions proposed
- Mental models or frameworks mentioned

#### 3. Decision Points
- Explicit agreements reached
- Resolved debates or choices made
- Selected approaches over alternatives
- Accepted constraints or limitations

#### 4. Question Points
- Open issues or concerns
- Topics requiring further clarification
- Uncertainties or ambiguities
- Dependencies on external factors

### Output Format

Generate a structured Key Points List in memory with the following structure:

```
=== KEY POINTS LIST ===

[Keywords]
- keyword1
- keyword2
- ...

[New Concepts]
- concept1: brief description
- concept2: brief description
- ...

[Decision Points]
- decision1: description
- decision2: description
- ...

[Question Points]
- question1: description
- question2: description
- ...
```

---

## Phase 3: Core Extraction & Categorization

### Goal

Organize the Key Points List into a three-dimensional structured format suitable for document generation.

### Classification Framework

Apply the following three dimensions to categorize all extracted content:

---

## Dimension 1: Business / Value

Focus on understanding the problem space and user needs.

### Pain Points
Extract and document:
- What problem are we solving?
- Why is the current solution inadequate?
- What frustrates users about existing approaches?
- What gaps in the market or workflow exist?

**Key Questions to Answer:**
- Who is experiencing the pain?
- When does the pain occur?
- What is the impact of not solving this?

### Core Interaction
Extract and document:
- How will users interact with the solution?
- What are the primary user actions?
- What are the key interface touchpoints?
- What is the user journey?

**Key Questions to Answer:**
- What does the user do first?
- What information does the user provide?
- What feedback does the user receive?
- How does the user complete their goal?

### Value Proposition
Extract and document:
- What makes this solution better than alternatives?
- What are the unique differentiators?
- What efficiency gains are expected?
- What is the competitive advantage?

**Key Questions to Answer:**
- Why would someone choose this over existing solutions?
- What metrics improve? (speed, cost, quality, satisfaction)
- What trade-offs are acceptable?

---

## Dimension 2: Technical / Architecture

Focus on understanding the implementation approach and system design.

### Data Flow
Extract and document:
- Where does data originate?
- How is data processed or transformed?
- Where is data stored or cached?
- How do different components exchange data?

**Key Questions to Answer:**
- What are the data sources?
- What is the data format?
- What are the processing steps?
- What are the data destinations?

### Key Components
Extract and document:
- What are the major system modules?
- How do components interact?
- What are the external dependencies?
- What is the deployment architecture?

**Key Questions to Answer:**
- What are the core services?
- How do components communicate?
- What are the integration points?
- What scales horizontally/vertically?

### Constraints
Extract and document:
- What technical limitations exist?
- What security considerations apply?
- What are the performance requirements?
- What are the platform/environment constraints?

**Key Questions to Answer:**
- What APIs or protocols must be used?
- What are the latency/throughput requirements?
- What security models apply?
- What compatibility requirements exist?

---

## Dimension 3: Specs / Constraints

Focus on defining concrete implementation details.

### Input/Output
Extract and document:
- What are the input formats or APIs?
- What are the output formats or responses?
- What are the parameter requirements?
- What are the error response formats?

**Key Questions to Answer:**
- What does the system accept as input?
- What does the system produce as output?
- What are the required vs optional fields?
- What are the validation rules?

### Directory Structure
Extract and document:
- Where should code files be placed?
- What is the configuration file layout?
- What are the asset organization rules?
- What is the deployment structure?

**Key Questions to Answer:**
- What is the root directory structure?
- Where do templates or static assets live?
- How are tests organized?
- What are the naming conventions?

### Error Handling
Extract and document:
- What happens when something goes wrong?
- How are errors reported to users?
- What are the recovery mechanisms?
- What are the fallback behaviors?

**Key Questions to Answer:**
- What error codes or messages exist?
- How are errors logged?
- Can the system recover automatically?
- What user guidance is provided on error?

---

## Output Format

Generate Structured Notes with the following format:

```
=== STRUCTURED NOTES ===

[Dimension 1: Business / Value]

Pain Points:
- [P1] Description...
- [P2] Description...

Core Interaction:
- [I1] Description...
- [I2] Description...

Value Proposition:
- [V1] Description...
- [V2] Description...

[Dimension 2: Technical / Architecture]

Data Flow:
- [D1] Description...
- [D2] Description...

Key Components:
- [C1] Description...
- [C2] Description...

Constraints:
- [T1] Description...
- [T2] Description...

[Dimension 3: Specs / Constraints]

Input/Output:
- [S1] Description...
- [S2] Description...

Directory Structure:
- [R1] Description...
- [R2] Description...

Error Handling:
- [E1] Description...
- [E2] Description...
```

---

## Extraction Guidelines

### Do:
- Be comprehensive - capture everything mentioned
- Preserve original terminology
- Note ambiguities or uncertainties
- Cross-reference related items across dimensions

### Don't:
- Filter out "unimportant" details
- Make assumptions beyond what's stated
- Ignore contradictory points (note them instead)
- Combine distinct concepts prematurely

---

## Transition to Phase 4

Once Structured Notes are complete, proceed to Phase 4 (Document Mapping) using `prompts/2_mapping.md`.
