---
name: how
description: Ground architecture in repository structure, behavior, constraints, and existing seams
---

# How: repository grounding

Establish how the relevant system works before proposing a design. Read the
smallest useful set of source, tests, configuration, and domain context; use
read-only `explore`, `researcher`, `test-investigation`, or `code-pattern` tasks
for bounded unknowns.

Distinguish observed behavior from interpretation. Cite repository paths and
relevant symbols, follow data and control flow, identify ownership, failure
modes, compatibility constraints, test seams, and conventions. Prefer existing
deep modules and proven seams over speculative restructuring. Record gaps as
unknowns, not facts.

## References

- [Explorer](explorer.md)
- [Explainer](explainer.md)
