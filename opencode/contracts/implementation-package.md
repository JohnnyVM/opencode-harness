# Implementation Package contract (version 2)

This is the complete, pasteable handoff to the Implementation Orchestrator.
Users and the Spec Orchestrator use the same template. Paste the filled-in
package text directly into the Implementation Orchestrator; a path, reference,
or request to develop a package is not an Implementation Package.

Validate the package before handoff with
`python3 ~/.config/opencode/scripts/validate_implementation_package.py < package.md`
(or the corresponding script in this repository). The validator checks shape;
the author remains responsible for the adequacy and truth of the decisions.

## Rules

- Include exactly one standalone `status: SPEC_APPROVED_BY_AGENT` or
  `status: SPEC_APPROVED_BY_USER`. The latter requires approval of this concrete
  package. Readiness does not authorize external writes.
- Fill every section below except Further Notes. Use `None` for no risks,
  unknowns, or out-of-scope items. Blocking product unknowns cannot be admitted.
- Tickets use unique `T` IDs; dependencies name existing tickets or `None`.
  Criteria name existing `AC` IDs. A ticket needs an objective, concrete allowed
  scope, forbidden scope, criteria, and an `Approach` describing what to build,
  key interfaces or files, and how dependent work fits together. Dependencies
  cannot form cycles. Every acceptance criterion must belong to a ticket.
- The complete package must let a worker implement each ticket using only its
  assigned package content and the repository. Move execution-relevant decisions
  from the specification conversation into this package. Do not use a previous
  package, conversation, or revision record as a source of missing requirements.
  A revision record is optional history; a revised package restates all current
  tickets, decisions, criteria, and checks. Superseded tickets are not active.
- The validator checks field presence and references, not whether the approach,
  scope, or verification genuinely suffices. Review each ticket from a worker's
  perspective before handoff.
- Each verification check needs an exact command, working directory,
  prerequisites, and expected result.
- Do not leave template placeholders, `TBD`, or `TODO` in a final package.
- Optional `target_repository` and `implementation_branch` fields may appear
  once each directly after `status`. When supplied, they constrain execution;
  the branch must differ from the repository's default branch.

## Copyable template

Replace the bracketed guidance and paste only the contents of the Markdown
code block (without its fences). Remove the optional Further Notes section if
unused.

```markdown
status: SPEC_APPROVED_BY_AGENT

## Problem Statement
[User-facing problem]

## Solution
[User-facing outcome]

## User Stories
1. As a [actor], I want [capability], so that [benefit].

## Implementation Decisions
- [Decisions, constraints and explicit assumptions]

## Testing Decisions
- [Behavioral testing seams and prior art]

## Tickets and Dependencies
### T1 — [Objective]
- Dependencies: None
- Allowed: [Files or directories]
- Forbidden: [Files or directories, or None]
- Criteria: AC1
- Approach: [Concrete implementation steps, files/interfaces and dependent output]

## Acceptance Criteria
- AC1: [Observable outcome]

## Verification Commands
### Local
#### L1 — [Check name]
- Command: `[exact command]`
- Working directory: [Directory relative to repository root]
- Prerequisites: [Setup or None]
- Expected: [Successful result]

## Risks
None identified

## Explicit Unknowns
None

## Out of Scope
None

## Further Notes
[Optional]
```
