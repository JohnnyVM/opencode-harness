# OpenCode Harness

This repository defines an OpenCode configuration for turning a complete
specification into a guarded, tested, and reviewed implementation.

## Language

**Spec Orchestrator**:
The user-facing agent that resolves requirements and produces a complete
Implementation Package.
_Avoid_: Lead, designer

**Implementation Package**:
The immutable validated snapshot of complete package text pasted into the
Implementation Orchestrator, containing the specification, tickets, dependencies,
acceptance criteria, Verification Matrix, risks, and unknowns used for one
implementation run. A completed package has exactly one readiness status,
`SPEC_APPROVED_BY_AGENT` or `SPEC_APPROVED_BY_USER`; either permits local
implementation without authorizing external writes. 
_Avoid_: Unvalidated input

**Implementation Orchestrator**:
The user-facing agent that coordinates execution of an Implementation Package
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
