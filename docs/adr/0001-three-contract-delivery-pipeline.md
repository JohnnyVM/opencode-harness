# ADR 0001: Split delivery into three validated contracts

## Status

Accepted

## Context

The former Implementation Package combined product requirements, architecture,
ticket planning, and worker dispatch details. Spec Orchestrator therefore made
code-structure decisions before a dedicated repository-grounding phase, while
Implementation Orchestrator reconstructed an informal coder packet that had no
machine-enforced shape.

## Decision

Use three independently versioned contracts:

1. Specification Package from Spec Orchestrator to model-neutral Architect.
2. Architecture Package from Architect to Implementation Orchestrator.
3. One Coder Assignment per ticket from Implementation Orchestrator to a coder.

The Architecture Package embeds its Specification Package unchanged. Product
gaps return to Spec Orchestrator; architecture and ticket gaps return to
Architect. `/architect`, `/implement`, and coder task dispatch validate the
contract crossing their seam. Legacy Implementation Package v2 input is not
accepted.

## Consequences

- Product and architecture ownership are explicit.
- `/implement` cannot start from a requirements-only artifact.
- Coders receive smaller, complete per-ticket context.
- Every specification revision invalidates derived Architecture Packages.
- Existing persisted v2 package fixtures must be replaced rather than silently
  admitted through compatibility code.
