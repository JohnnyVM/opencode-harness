# OpenCode Harness

This repository defines an OpenCode configuration for turning an approved
specification into a guarded, tested, and reviewed implementation.

## Language

**Spec Design**:
The user-facing agent that resolves requirements and produces an approved
Implementation Package.
_Avoid_: Lead, orchestrator

**Implementation Package**:
The approved specification, tickets, dependencies, acceptance criteria,
verification matrix, risks, unknowns, and authorization supplied for execution.
_Avoid_: Prompt, task description

**Implementation Orchestrator**:
The user-facing agent that coordinates execution of an Implementation Package
through leaf workers.
_Avoid_: Lead, coder

**Worker**:
A delegated coder, Debugger, Tester, or Code Reviewer that performs one bounded
assignment and cannot delegate further.
_Avoid_: Nested agent

**Verification Matrix**:
The complete set of approved local and remote checks required for an
implementation commit.
_Avoid_: Tests, when referring to the full gate

**Testing Sweep**:
One execution of the complete Verification Matrix, producing a consolidated
result rather than stopping after the first independent failure.
_Avoid_: Test loop

**Guarded Repository Lifecycle**:
The admission, branch, commit, integration, and drift rules that preserve work
while the Implementation Package is executed.
_Avoid_: Git automation
