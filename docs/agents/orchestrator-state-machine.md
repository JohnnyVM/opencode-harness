# Implementation Orchestrator State Machine

This document is the authoritative workflow and repository-lifecycle contract
for the Implementation Orchestrator. The agent definition in
[`implementation-orchestrator.md`](../../opencode/agents/implementation-orchestrator.md)
implements this contract.

## States

The Orchestrator tracks exactly one state:

1. `SPEC_RECEIVED`: an approved implementation package was supplied.
2. `PLANNING`: tickets, dependencies, scopes, and checks are being scheduled.
3. `IMPLEMENTING`: exactly one bounded coder assignment is active.
4. `TESTING`: the Tester is running the complete local and remote matrix.
5. `DEBUGGING`: the Debugger is analyzing one consolidated failure report.
6. `REVIEWING`: the Code Reviewer is reviewing a Tester-approved commit.
7. `FINALIZING`: repository lifecycle checks and guarded integration are running.
8. `BLOCKED_SPEC`: the package is missing or contradicts a required decision.
9. `BLOCKED_IMPLEMENTATION`: implementation or infrastructure cannot proceed.
10. `BLOCKED_OPERATION`: repository lifecycle or execution safety was violated.
11. `BLOCKED_DIAGNOSIS`: root cause could not be established within budget.
12. `DONE`: testing, review, and final lifecycle checks all passed.

## Transitions

```text
SPEC_RECEIVED -> PLANNING -> IMPLEMENTING -> TESTING
TESTING -- PASS --> REVIEWING
TESTING -- FAIL --> DEBUGGING
TESTING -- CONFIG_MISSING --> BLOCKED_SPEC
TESTING -- INFRA_BLOCKED after retry --> BLOCKED_IMPLEMENTATION
DEBUGGING -- code_or_test_problem --> IMPLEMENTING
DEBUGGING -- design_or_spec_problem --> BLOCKED_SPEC
DEBUGGING -- environment_problem --> BLOCKED_IMPLEMENTATION
DEBUGGING -- inconclusive --> BLOCKED_DIAGNOSIS
REVIEWING -- changes_required --> IMPLEMENTING
REVIEWING -- debugging_required --> DEBUGGING
REVIEWING -- testing_not_passed --> TESTING
REVIEWING -- approved --> FINALIZING
FINALIZING -- lifecycle_pass --> DONE
FINALIZING -- lifecycle_failure --> BLOCKED_OPERATION
Any non-terminal state -- guarded repository/execution violation --> BLOCKED_OPERATION
BLOCKED_SPEC --> SPEC_RECEIVED after specification resolution
BLOCKED_IMPLEMENTATION --> PLANNING when resolved
BLOCKED_OPERATION --> PLANNING after operator resolution and fresh admission
DONE --> terminal
```

Only specification problems return to Spec Design. Operational,
infrastructure, and diagnostic blockers return directly to the user or
operator.

## Delegation Invariants

- At most one coder, Debugger, Tester, or Code Reviewer is active at a time.
- Every delegated agent is a leaf and cannot delegate further.
- `subagent_depth` remains `1`.
- The Code Reviewer is invoked only after the Tester returns `PASS` for the
  exact implementation commit.
- Any change after testing invalidates the Tester result and review approval.

## Testing Gate

The Tester runs every required local and remote check in one sweep. Independent
checks continue after failures so one report captures the full failure set.
Checks blocked by a failed prerequisite are recorded as skipped rather than
silently omitted.

Results are:

- `PASS`: every required check passed, or remote verification was explicitly
  approved as not applicable.
- `FAIL`: one or more checks found a project, test, build, static-analysis,
  acceptance, or remote-CI failure.
- `INFRA_BLOCKED`: infrastructure prevented meaningful execution.
- `CONFIG_MISSING`: required commands, prerequisites, remote rationale, or
  commit identity were absent.

One consolidated Tester failure report is sent to the Debugger. Confirmed code
and test problems become one bounded correction assignment, not one assignment
per error. Every correction requires the complete testing matrix to run again.

## Guarded Repository Lifecycle

Before planning, when the run creates an implementation branch from the
original/default branch, the Orchestrator captures the original branch/ref and
exact tip. It admits only a clean worktree: staged, unstaged, and untracked
files block admission; ignored files are permitted. Detached HEAD, unresolved
default branch, active operations, locks, and ambiguous ref/index/metadata
states also block admission.

On the default branch, the Orchestrator creates and switches to the approved
implementation branch. A clean usable non-default branch is used as-is and has
no original-branch integration. The admitted branch and immutable commit
baseline are recorded.

Immediately before every delegation, the Orchestrator validates the current
branch and exact expected tip. Assignments include the admitted branch,
immutable baseline, current expected tip, and allowed and forbidden scopes.
Coders do not inspect Git metadata or issue Git commands. The Orchestrator alone
stages and creates meaningful issue-linked commits after coder-local checks
pass.

Unexpected branch, ref, index, metadata, untracked-file, or out-of-scope drift
stops non-destructively as `BLOCKED_OPERATION`. Never reset, clean,
force-update, overwrite, rebase, stash, or discard preserved work.

Remote publication or workflow setup is allowed only when the approved package
names the exact remote, ref, operation, and authorization. No other push,
deployment, or external write is allowed.

After Code Reviewer approval, `FINALIZING` validates that the reviewed commit,
branch, original baseline, and clean worktree still match. When an
implementation branch was created from the original/default branch, guarded
integration advances the original branch by fast-forward only. A non-default
branch used as-is is already the implementation result. Any mismatch or
integration failure is `BLOCKED_OPERATION`; the implementation branch, commits,
and worktree are preserved.

Every `BLOCKED_OPERATION` report includes the failed operation, expected and
observed state, completed checks, preserved branch/commit/worktree state, and
the exact retry or operator action.

## Budgets

For each consolidated testing sweep, allow at most two Debugger investigations,
two consolidated correction attempts after initial implementation, one
qwen-to-gpt reassignment, and one infrastructure retry. Reset a budget only for
a materially different failure signature or confirmed root cause.
