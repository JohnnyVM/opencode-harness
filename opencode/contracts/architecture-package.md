# Architecture Package contract (version 2)

This is the complete, pasteable handoff from Architect to Implementation
Orchestrator. `/implement` accepts only this version. Version 1 packages must be
regenerated; there is no migration or dual-format mode.

Validate with:

```bash
python3 opencode/scripts/validate_architecture_package.py < architecture.md
python3 opencode/scripts/validate_architecture_package.py --specification specification.md < architecture.md
```

The validator checks structure, identifiers, requirement traceability, ticket
dependencies, verification fields, and optionally byte-for-byte specification
preservation. Architect remains responsible for feasibility and design quality.

## Required structure

The package has exactly the following ordered level-two sections:

1. Decision Summary
2. Repository Findings
3. Architecture Candidates
4. Comparison and Recommendation
5. Proposed Design
6. Interfaces and Behavior
7. Implementation Plan
8. Testing Strategy
9. Verification Matrix
10. Requirements Traceability
11. Risks and Open Questions
12. Frozen Specification

Use stable identifiers: `C1`… for candidates, `D1`… for significant design
decisions, `T1`… for tickets, and `L1`… for verification checks. Every
acceptance criterion must trace to at least one decision, ticket, and check.

## Rules

- Begin with exactly `package-version: 2` and one `status: ARCHITECTURE_READY`.
- Preserve the complete validated Specification Package byte-for-byte between
  the reserved markers in the final section. Do not revise its requirements.
- Give repository findings concrete file/behavior evidence; label inference and
  uncertainty rather than presenting them as verified facts.
- Include at least two structurally distinct candidates with responsibilities,
  flow, interfaces, requirement fit, benefits, costs, and risks.
- Compare candidates against relevant explicit criteria and explain the selected
  design and rejected alternatives. Do not use unexplained numeric scores.
- Keep each section focused on its stated purpose; avoid duplicating rationale.
- Tickets use unique `T` IDs, form an acyclic dependency graph, reference valid
  acceptance criteria, name concrete allowed paths, describe implementation
  steps, and state produced outputs.
- Each verification check has a runnable command, working directory,
  prerequisites, and observable expected result.
- Traceability rows use the exact form `| AC1 | D1 | T1 | L1 |`; IDs may be
  comma-separated. Every criterion in the frozen specification must have a row.
- Architecture unknowns cannot be blocking. Return product gaps to Spec
  Orchestrator and architecture gaps to Architect instead of guessing.
- Do not leave template placeholders, `TODO`, or `TBD` in a final package.

## Copyable template

```markdown
package-version: 2
status: ARCHITECTURE_READY

## Decision Summary

**Recommendation:** {{One-sentence chosen design}}
**Reasons:** {{Two or three decisive reasons}}
**Change scope:** {{Affected modules and approximate ticket count}}
**Principal trade-off:** {{Benefit accepted and cost incurred}}
**Primary risk:** {{Most important risk or None}}

## Repository Findings

| Finding | Evidence | Status |
|---|---|---|
| {{Existing behavior or seam}} | `path/to/file` — {{observed fact}} | Verified |
| {{Constraint or inference}} | {{Evidence}} | Inferred |

## Architecture Candidates

### C1 — {{Candidate name}}
- Structure and ownership: {{Responsibilities and boundaries}}
- Flow: {{Data/control flow}}
- Interfaces: {{Existing and new interfaces}}
- Requirement fit: {{Relevant AC IDs and any shortfall}}
- Benefits: {{Benefits}}
- Costs and risks: {{Costs and risks}}

### C2 — {{Structurally distinct candidate name}}
- Structure and ownership: {{Responsibilities and boundaries}}
- Flow: {{Data/control flow}}
- Interfaces: {{Existing and new interfaces}}
- Requirement fit: {{Relevant AC IDs and any shortfall}}
- Benefits: {{Benefits}}
- Costs and risks: {{Costs and risks}}

## Comparison and Recommendation

| Criterion | C1 — {{name}} | C2 — {{name}} |
|---|---|---|
| Requirement fit | {{Evidence-based assessment}} | {{Assessment}} |
| Repository fit | {{Assessment}} | {{Assessment}} |
| Interface and change locality | {{Assessment}} | {{Assessment}} |
| Testability and failure behavior | {{Assessment}} | {{Assessment}} |

**Selected:** {{Candidate or synthesis}}
**Rationale:** {{Why it wins; what is retained or rejected}}

## Proposed Design

### D1 — {{Significant decision}}
- Decision: {{Chosen design and scope}}
- Evidence: {{Repository paths, specification clauses, or sources}}
- Alternatives: {{Meaningful alternatives}}
- Trade-offs: {{Benefits, costs, constraints}}
- Consequences: {{Interfaces, ownership, migration, verification}}
- Evidence basis: {{Verified fact, inference, or assumption}}

### Responsibilities and flow
{{Module responsibilities, dependency direction, and end-to-end flow}}

## Interfaces and Behavior

{{Caller-first examples, signatures/types, invariants, error modes, and
compatibility behavior. State explicitly when no public interface changes.}}

## Implementation Plan

### T1 — {{Objective}}
- Dependencies: None
- Allowed: {{Concrete paths}}
- Forbidden: {{Scope or None}}
- Criteria: AC1
- Approach: {{Concrete implementation steps}}
- Outputs: {{Artifacts/behavior and handoff needed downstream}}

## Testing Strategy

{{Existing coverage to reuse, additions, test granularity, and any test-first
sequencing. Connect each criterion to at least one verification check below.}}

## Verification Matrix

### Local
#### L1 — {{Check name}}
- Command: `{{Exact command}}`
- Working directory: {{Directory relative to repository root}}
- Prerequisites: {{None or exact prerequisites}}
- Expected: {{Observable successful result}}

## Requirements Traceability

| Criterion | Design decisions | Tickets | Verification |
|---|---|---|---|
| AC1 | D1 | T1 | L1 |

## Risks and Open Questions

### Risks
- R1 — {{Risk and impact}}; mitigation/detection: {{Action or check}}.

### Open questions
- Q1 — {{Non-blocking uncertainty}}; resolution: {{How/when it will be resolved}}.

## Frozen Specification
<!-- BEGIN SPECIFICATION PACKAGE -->
{{Complete validated Specification Package, unchanged}}
<!-- END SPECIFICATION PACKAGE -->
```
