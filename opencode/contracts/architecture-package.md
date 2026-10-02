# Architecture Package contract (version 1)

This is the complete, pasteable handoff from Architect to Implementation
Orchestrator. `/implement` accepts only this contract.

Validate it with
`python3 ~/.config/opencode/scripts/validate_architecture_package.py < architecture.md`.
During architecture generation, also pass
`--specification <original-specification-path>` to verify byte-for-byte preservation.
The validator checks shape and references; the Architect remains responsible
for feasibility and the adequacy of the design.

## Rules

- Include exactly one outer `status: ARCHITECTURE_READY`.
- Embed one complete validated Specification Package byte-for-byte between the
  reserved markers. Do not revise its status, decisions, or acceptance criteria.
- Tickets use unique `T` IDs, form an acyclic dependency graph, and reference
  acceptance criteria from the embedded specification.
- Every acceptance criterion belongs to at least one ticket.
- `Allowed` names concrete paths. Use `None` for absent dependencies or
  forbidden scope, not for allowed scope or implementation approach.
- The Verification Matrix contains exact commands, working directories,
  prerequisites, and expected results.
- Architecture unknowns cannot be blocking. Return product gaps to Spec
  Orchestrator and architecture gaps to Architect instead of guessing.
- Do not leave template placeholders, `TODO`, or `TBD` in a final package.

## Copyable template

```markdown
status: ARCHITECTURE_READY

<!-- BEGIN SPECIFICATION PACKAGE -->
{{Complete validated Specification Package, unchanged}}
<!-- END SPECIFICATION PACKAGE -->

## Architecture Summary
{{Chosen shape and why it satisfies the frozen specification}}

## Usage and Interface Sketch
{{Caller-first examples, types, signatures, invariants, and error modes}}

## Structural Decisions
- {{Modules, responsibilities, seams, dependency direction, and rationale}}

## Implementation Decisions
- {{Concrete repository decisions and constraints}}

## Testing Strategy
- {{Test seams, existing coverage to reuse, and required additions}}

## Tickets and Dependencies
### T1 — {{Objective}}
- Dependencies: None
- Allowed: {{Concrete files or directories}}
- Forbidden: None
- Criteria: AC1
- Approach: {{Concrete implementation steps and dependency outputs}}

## Verification Matrix
### Local
#### L1 — {{Check name}}
- Command: `{{Exact command}}`
- Working directory: {{Directory relative to repository root}}
- Prerequisites: None
- Expected: {{Observable successful result}}

## Architecture Risks
None

## Architecture Unknowns
None
```
