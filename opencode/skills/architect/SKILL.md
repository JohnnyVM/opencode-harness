---
name: architect
description: Shared workflow and package contract for repository-grounded architecture design
---

# Architect

The Architecture Orchestrator accepts a validated Specification Package and
produces an Architecture Package, without implementing production code.

## Package rules

- Produce Architecture Package version 2 only; version 1 is retired and must be
  regenerated, not migrated or accepted as a second format.
- Preserve and reproduce the input Specification Package verbatim as a frozen
  final section. Never revise its requirements while designing.
- Ground decisions in repository evidence; mark assumptions, inferences, and
  unknowns explicitly.
- Follow the ordered v2 contract template: Decision Summary, Repository Findings,
  Architecture Candidates, Comparison and Recommendation, Proposed Design,
  Interfaces and Behavior, Implementation Plan, Testing Strategy, Verification
  Matrix, Requirements Traceability, Risks and Open Questions, Frozen
  Specification.
- Include at least two structurally distinct candidates, compare them using
  explicit relevant criteria, and explain the recommendation without unexplained
  scores.
- Use stable C/D/T/L identifiers. Every acceptance criterion must trace to at
  least one design decision, implementation ticket, and verification check.
- Record implementation ticket outputs and exact runnable verification details.
- Keep the report concise and decision-first; avoid repeating the same rationale
  across sections.
- Write only to the user's explicit output path. Validate with the available
  validator and report exactly what was or was not checked.
- A design review may challenge the result but must not edit it. No claim of
  multi-model review absent actual independent models.

## References

- [Runner prompt](runner-prompt.md)
- [Rationale template](rationale-template.md)
- [Design red flags](design-red-flags.md)

Adapted for OpenCode from the public `cursor/plugins` architecture-design
source, accessed 2026-09-30. No upstream commit/revision was verified; no hash
is claimed. Upstream source is MIT-licensed; this adaptation retains that
attribution. See [LICENSE-ATTRIBUTION.md](LICENSE-ATTRIBUTION.md).
