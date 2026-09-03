# OpenCode Harness: Implementation Orchestrator Workflow

## Overview

The Implementation Orchestrator is a subagent invoked by the Engineering Lead to execute approved implementation packages. It manages the end-to-end workflow from specification receipt through implementation, verification, debugging, and review.

## Workflow States

The orchestrator tracks exactly one state at all times. The following states are defined:

1. **SPEC_RECEIVED** - Initial state when an approved package is received from the Lead
2. **PLANNING** - When the spec is complete enough to schedule implementation
3. **IMPLEMENTING** - When exactly one bounded coder ticket is active at a time
4. **VERIFYING** - When coder work is complete and integrated, awaiting verification
5. **DEBUGGING** - When required verification failed and debugging is needed
6. **REVIEWING** - When verification passes and review is required
7. **BLOCKED_SPEC** - When a missing/conflicting design or requirement is found
8. **BLOCKED_IMPLEMENTATION** - When a coder cannot complete a bounded ticket
9. **BLOCKED_OPERATION** - When guarded repository lifecycle or execution invariants detect drift or an unsafe/ambiguous operation
10. **BLOCKED_DIAGNOSIS** - When root cause cannot be established within budget
11. **DONE** - Terminal state when verification passes and review approves

## State Transitions

```
SPEC_RECEIVED -> PLANNING -> IMPLEMENTING -> VERIFYING
VERIFYING -- pass --> REVIEWING
VERIFYING -- fail --> DEBUGGING
DEBUGGING -- code_problem --> IMPLEMENTING -> VERIFYING
DEBUGGING -- design_or_spec_problem --> BLOCKED_SPEC
DEBUGGING -- environment_problem --> BLOCKED_IMPLEMENTATION (after environment correction)
DEBUGGING -- inconclusive --> BLOCKED_DIAGNOSIS
Any non-terminal state -- guarded repository/execution violation --> BLOCKED_OPERATION
REVIEWING -- correction_clear --> IMPLEMENTING -> VERIFYING
REVIEWING -- unexplained_failure --> DEBUGGING
REVIEWING -- approved --> DONE
BLOCKED_SPEC --> SPEC_RECEIVED (after Lead resolution)
BLOCKED_IMPLEMENTATION --> PLANNING (if resolvable) or escalates
BLOCKED_OPERATION --> PLANNING (only after Lead/operator resolution and fresh admission)
BLOCKED_DIAGNOSIS --> escalates
DONE --> terminal
```

## Result Classifications

Verification results are classified as:
- `PASS` - All required checks succeeded
- `FAIL` - Behavior, tests, build, static analysis, or acceptance checks failed
- `INFRA_BLOCKED` - Infrastructure, credentials, dependencies, or runner failure prevented meaningful execution

## Handling of Special Cases

### INFRA_BLOCKED
- May be retried once after concrete infrastructure correction
- If still blocked after retry, transition to appropriate blocking state with exact dependency/operator action

### ENVIRONMENT_PROBLEM
- Must not cause unsupported source-code workaround
- Routes to BLOCKED_IMPLEMENTATION with exact operator action required
- May retry once after environment correction

### INCONCLUSIVE
- Must transition to BLOCKED_DIAGNOSIS
- Returns Debug Report plus smallest missing evidence/access requirement to Lead
- No speculative coder ticket is created

## Invariants

- Only one state is tracked at any time
- Reviewer is never invoked directly after coding without passing verification
- All transitions use only legal existing state names
- Retry budgets are enforced per distinct verification failure
- Escalation states are used when retry budgets are exhausted

## Guarded repository lifecycle

Before planning, the Orchestrator admits the repository only when the
worktree is clean: no staged, unstaged, or untracked files are permitted
(ignored files are permitted). It rejects detached HEAD, an unresolved default
branch, active or incomplete operations, lock files, and any ambiguous ref,
index, or metadata state. On the default branch it creates and switches to the
implementation branch; on a clean usable non-default branch it keeps that
branch. It records the admitted branch and exact commit baseline.

Coders run sequentially in the admitted working tree. Each assignment names
the admitted branch and commit plus exact allowed and forbidden scopes. Coders
must not run direct Git commands or modify `.git`; this is accidental
protection, not a sandbox. The Orchestrator alone performs explicit staging and
meaningful, non-empty issue-linked commits identifying the approved issue or
ticket, after unit checks pass.

The Orchestrator stops non-destructively on unexpected branch/ref/index/
metadata/untracked or out-of-scope drift, preserving all changes and
reporting `BLOCKED_OPERATION`. Baseline capture and restoration use guarded
fast-forward-only operations. A clean tip is required before final
verification and review; any later drift invalidates those results.

`BLOCKED_OPERATION` reports the lifecycle stage, admitted branch and baseline
commit, expected and observed branch/ref/index/metadata/worktree state, exact
drift or unsafe operation, preserved-change status, and required Lead/operator
resolution before fresh admission. It is distinct from `BLOCKED_SPEC`,
`BLOCKED_IMPLEMENTATION`, and `BLOCKED_DIAGNOSIS`.
