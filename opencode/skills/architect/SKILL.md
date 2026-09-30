---
name: architect
description: Shared workflow and package contract for repository-grounded architecture design
---

# Architect

The Architecture Orchestrator accepts a validated Specification Package and
produces an Architecture Package, without implementing production code.

## Package rules

- Preserve and reproduce the input Specification Package verbatim as a frozen
  section. Never revise its requirements while designing.
- Ground decisions in repository evidence; mark assumptions, inferences, and
  unknowns explicitly.
- Include at least two structurally distinct candidates, a comparison using
  stated criteria, and a reasoned synthesis.
- Record important interfaces/seams, responsibilities, flows, constraints,
  risks, trade-offs, and implementation-facing guidance.
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
