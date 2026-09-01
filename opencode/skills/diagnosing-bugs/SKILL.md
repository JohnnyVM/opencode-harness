---
name: diagnosing-bugs
description: Diagnose a reported defect by reproducing it, tracing the execution path, and identifying the root cause. Use when the user reports a bug, error, failure, regression, or unexpected behavior.
---

# Diagnosing Bugs

Treat the report as a hypothesis, not a diagnosis.

1. Establish the expected and observed behavior.
2. Reproduce the failure with the smallest reliable case.
3. Inspect logs, tests, recent changes, and the relevant execution path.
4. Identify the root cause and distinguish it from symptoms.
5. Add or update a regression test at the highest appropriate seam.
6. Make the smallest fix, then verify the focused and relevant broader tests.

When reproduction is unavailable, state what was checked, what remains uncertain, and what evidence would resolve it.
