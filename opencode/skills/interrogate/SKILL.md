---
name: interrogate
description: Optionally stress-test an architecture recommendation and return a verdict without edits
---

# Interrogate: optional verdict

Review the frozen requirements, repository evidence, candidates, comparison,
and synthesis. Look for unmet requirements, unsupported claims, hidden coupling,
unclear ownership or failure behavior, migration and compatibility gaps, and
verification omissions. Return a concise verdict—accept, accept with concerns,
or revise—with evidence and prioritized objections. This is advisory scrutiny,
not an independent or multi-model review unless that is genuinely the case.

Do not edit files, rewrite the package, or implement code. The architect owns
the response to the verdict.

## References

- [Reviewer](reviewer.md)
- [Rubric](rubric.md)
- [Code quality](code-quality.md)
- [Lead judgment](lead-judgment.md)
