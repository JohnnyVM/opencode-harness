# OpenCode Harness

This repository defines an OpenCode configuration for turning a complete
specification into a guarded, tested, and reviewed implementation.

## Language

**Evaluation Case**:
A versioned, repository-local manifest describing one reproducible orchestrator
evaluation. Version 1 currently supports only `guadalbot-46`.

**Command Record**:
One strictly validated argv and expectation record in an Evaluation Case.

**Evaluation Status**:
The finite status value reported for an evaluation or command; it is not a
free-form lifecycle or plugin extension point.

**Exit Code**:
The process result represented by a non-negative integer, with `0` meaning
success and `2` reserved for invalid CLI input or case data.

**Spec Design**:
The user-facing agent that resolves requirements and produces a complete
Implementation Package.
_Avoid_: Lead, orchestrator

**Implementation Package**:
The immutable validated snapshot of an open GitHub Issue containing the
complete specification, tickets, dependencies, acceptance criteria,
Verification Matrix, risks, and unknowns used for one implementation run. Its
Issue Reference determines the target repository; an
optional `target_repository` may repeat that identity as a consistency
assertion. An optional exact `implementation_branch` may constrain execution;
otherwise a clean current non-default branch becomes the admitted
implementation branch.
_Avoid_: Prompt, task description, copied package

**Issue Reference**:
Exactly one durable locator for an Implementation Package: `#<number>` in the
current repository, `<owner>/<repository>#<number>`, or a GitHub issue URL.
_Avoid_: Package text

**Implementation Orchestrator**:
The user-facing agent that coordinates execution of an Implementation Package
through leaf workers.
_Avoid_: Lead, coder

**Worker**:
A delegated coder, Debugger, Tester, Code Reviewer, or Cleaner that performs
one bounded assignment and cannot delegate further.
_Avoid_: Nested agent

**Verification Matrix**:
The complete set of approved local and remote checks required for an
implementation. Coders may run focused development checks, but only Tester
results approve supplied portions of this matrix.
_Avoid_: Tests, when referring to the full gate

**Implementation Candidate**:
The expected accumulated, uncommitted changes produced by sequential initial
tickets and certified by the local Testing Sweep before the first
implementation commit.
_Avoid_: Staged tree, when referring to the pre-commit candidate

**Testing Sweep**:
One Tester invocation over a supplied local or remote portion of the
Verification Matrix, producing a consolidated result for that complete scope
rather than stopping after the first independent failure.
_Avoid_: Test loop

**Guarded Repository Lifecycle**:
The admission, branch, commit, integration, and drift rules that preserve work
while the Implementation Package is executed.
_Avoid_: Git automation
