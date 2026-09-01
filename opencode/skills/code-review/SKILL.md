---
name: code-review
description: Review code or a change for bugs, regressions, security risks, and missing tests. Use when the user asks for a review, audit, critique, or feedback on a diff or implementation.
---

# Code Review

Review from the perspective of a maintainer responsible for correctness in production.

Prioritize findings over summaries. Check behavior, error paths, boundaries, compatibility, security, performance, and test coverage. Report findings ordered by severity with precise file and line references. Explain the failure mode and, where useful, the smallest corrective direction. Do not report style preferences as findings unless they affect correctness or project conventions.

If no findings are present, say so explicitly and identify meaningful residual testing gaps or risks.
