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

Before planning, when the run creates an implementation branch from the
original/default branch, the Orchestrator captures that original branch/ref
and exact tip baseline before creating the implementation branch. It admits
the repository only when the worktree is clean: no staged, unstaged, or
untracked files are permitted (ignored files are permitted). It rejects
detached HEAD, an unresolved default branch, active or incomplete operations,
lock files, and any ambiguous ref, index, or metadata state. On the default
branch it creates and switches to the implementation branch; on a clean usable
non-default branch it keeps that branch as-is: that branch is the
implementation tip and there is no original-branch integration. It records
the implementation branch and exact immutable admitted commit baseline.

Coders run sequentially in the admitted working tree. Immediately before
each delegation, the Orchestrator alone validates that the current branch and
exact current tip match the assignment's admitted branch and expected tip; a
mismatch blocks delegation. Each assignment provides the admitted branch,
immutable admitted baseline, exact current expected implementation tip, and
exact allowed and forbidden scopes as immutable context. The immutable
baseline is lifecycle history, not necessarily the current tip for a later
sequential ticket. Coders validate assignment completeness and allowed scope
before editing and obey the scope; they do not inspect repository Git or
metadata. Coders must not run direct Git commands or modify `.git`; this is
accidental protection, not a sandbox. The Orchestrator alone performs explicit
staging and meaningful, non-empty issue-linked commits identifying the
approved issue or ticket, after unit checks pass.

The Orchestrator stops non-destructively on unexpected branch/ref/index/
metadata/untracked or out-of-scope drift, preserving all changes and
reporting `BLOCKED_OPERATION`. Baseline capture and restoration use guarded
fast-forward-only operations. A clean tip is required before final
verification and review; any later drift invalidates those results.

After reviewer approval, if the run created an implementation branch from the
original/default branch, guarded integration first validates that the original
branch/ref is exactly the captured baseline, the implementation branch/HEAD
exactly equals the reviewed commit, and the worktree is clean. It uses
fast-forward only to advance the original branch to the reviewed tip, and
validates the final original branch/HEAD is the clean reviewed tip. For a clean
non-default branch used as-is, the reviewed implementation tip is already the
implementation result and no original-branch integration occurs. Any mismatch,
drift, or integration failure is `BLOCKED_OPERATION`; preserve the
implementation branch, commits, and worktree and perform no merge, rebase,
force-update, reset, restore, clean, stash, push, or branch deletion.

Every `BLOCKED_OPERATION` report includes: failed operation; expected vs
observed state; completed checks; preserved branch/commit/worktree state; and
the exact retry/operator action. Task crashes/cancellations and
invocation/tool failures route to `BLOCKED_OPERATION`, alongside unsafe
admission or lifecycle drift. It is distinct from `BLOCKED_SPEC`,
`BLOCKED_IMPLEMENTATION`, and `BLOCKED_DIAGNOSIS`.
