# Specification Package contract (version 1)

This is the complete, pasteable handoff from Spec Orchestrator to Architect.
It freezes product intent and observable acceptance without choosing the code
structure that will implement it.

Validate it with
`python3 ~/.config/opencode/scripts/validate_specification_package.py < specification.md`.
The validator checks shape; the author remains responsible for truth and
completeness.

## Rules

- Include exactly one `status: SPEC_APPROVED_BY_AGENT` or
  `status: SPEC_APPROVED_BY_USER`. User approval applies only to this exact
  text. Neither status authorizes external writes.
- Fill every section. Use `None` when there is no risk, unknown, or out-of-scope
  behavior.
- Acceptance criteria use unique `AC` IDs and describe observable outcomes.
- Explicit unknowns may be non-blocking only. Resolve product decisions needed
  for architecture before approval.
- Do not include architecture, interfaces, tickets, paths, implementation
  approaches, or executable verification commands.
- Do not leave template placeholders, `TODO`, or `TBD` in a final package.

## Copyable template

```markdown
status: SPEC_APPROVED_BY_AGENT

## Problem Statement
{{User-facing problem}}

## Solution
{{User-facing outcome}}

## User Stories
1. As a {{actor}}, I want {{capability}}, so that {{benefit}}.

## Product Decisions and Constraints
- {{Behavior, invariant, compatibility requirement, or explicit assumption}}

## Testing Decisions
- {{Behavioral seam and evidence needed to demonstrate the outcome}}

## Acceptance Criteria
- AC1: {{Observable outcome}}

## Risks
None

## Explicit Unknowns
None

## Out of Scope
None
```
