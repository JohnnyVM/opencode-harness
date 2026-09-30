# OpenCode Harness

This repository defines an OpenCode configuration for turning a complete
specification into a guarded, tested, and reviewed implementation.

## Language

**Spec Orchestrator**:
The user-facing agent that resolves requirements and produces a complete
Specification Package.
_Avoid_: Lead, designer

**Specification Package**:
The immutable validated product handoff from Spec Orchestrator to Architect. It
contains behavior, constraints, test intent, acceptance criteria, risks, and
unknowns, but no architecture or implementation plan. Its readiness status is
`SPEC_APPROVED_BY_AGENT` or `SPEC_APPROVED_BY_USER`.
_Avoid_: Implementation Package

**Architect**:
The model-neutral user-facing agent that grounds a frozen Specification Package
in the repository and produces an Architecture Package. Architect does not
implement production code or change product requirements.
_Avoid_: Coder, Spec Orchestrator

**Architecture Package**:
The immutable validated snapshot accepted by `/implement`. It embeds the exact
Specification Package and adds the selected architecture, tickets,
dependencies, path scope, test strategy, and Verification Matrix for one run.
Its readiness status is `ARCHITECTURE_READY`.
_Avoid_: Specification Package, Implementation Package

**Coder Assignment**:
The validated, self-contained, per-ticket handoff from Implementation
Orchestrator to one coder. It contains relevant frozen specification and
architecture decisions, exact scope and criteria, focused checks, repository
snapshot, dependency outputs, and test-first evidence.
_Avoid_: Prompt, partial ticket reference

**Implementation Orchestrator**:
The user-facing agent that coordinates execution of an Architecture Package
through leaf workers.
_Avoid_: Lead, coder

**Worker**:
A delegated coder, Debugger, Tester, Code Reviewer, or Cleaner that performs
one bounded assignment and cannot delegate further.
_Avoid_: Nested agent

**Verification Matrix**:
The complete set of approved verification checks required for an
implementation. Coders may run focused development checks, but only Tester
results approve this matrix.
_Avoid_: Tests, when referring to the full gate

**Implementation Candidate**:
The expected accumulated changes produced by sequential initial
tickets and certified by the local Testing Sweep
_Avoid_: Staged tree, when referring to the pre-commit candidate

**Testing Sweep**:
One Tester invocation over the Verification Matrix, producing a consolidated result for the complete scope
rather than stopping after the first independent failure.
_Avoid_: Test loop
