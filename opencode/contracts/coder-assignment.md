# Coder Assignment contract (version 1)

This is the complete per-ticket handoff from Implementation Orchestrator to a
coder. The task-dispatch plugin rejects coder prompts that do not satisfy this
contract.

Validate it with
`python3 ~/.config/opencode/scripts/validate_coder_assignment.py < assignment.md`.

## Rules

- Include exactly one `status: ASSIGNMENT_READY`.
- Include one ticket only. Copy its objective, scope, and approach from the
  admitted Architecture Package.
- Include the complete text of every referenced acceptance criterion and only
  the specification and architecture decisions relevant to this ticket.
- Every focused check includes command, working directory, prerequisites, and
  expected result.
- Record the admitted branch, immutable baseline, expected current `HEAD`,
  expected existing candidate, and any additional approved scope.
- Include completed dependency outputs. A test-first dependent ticket includes
  the actual red command, working directory, status, and intended assertion
  evidence.
- Use `None` explicitly when dependency outputs, candidate changes, additional
  scope, or test-first evidence do not apply.
- Do not leave template placeholders, `TODO`, or `TBD` in a final assignment.

## Copyable template

```markdown
status: ASSIGNMENT_READY

## Objective
{{Ticket ID and objective}}

## Relevant Specification
{{Relevant frozen decisions and constraints}}

## Relevant Architecture
{{Relevant structural and implementation decisions}}

## Ticket Scope
- Ticket: T1
- Dependencies: None
- Allowed: {{Concrete files or directories}}
- Forbidden: None
- Approach: {{Complete ticket approach}}

## Acceptance Criteria
- AC1: {{Verbatim criterion}}

## Test Strategy
{{Required test behavior and red/green sequencing}}

## Focused Checks
### C1 — {{Check name}}
- Command: `{{Exact command}}`
- Working directory: {{Directory relative to repository root}}
- Prerequisites: None
- Expected: {{Observable result}}

## Repository Snapshot
- Branch: {{Admitted implementation branch}}
- Baseline: {{Immutable commit SHA}}
- Expected HEAD: {{Current commit SHA}}
- Expected candidate: None
- Additional allowed scope: None

## Dependency Outputs
None

## Test-First Evidence
None
```
