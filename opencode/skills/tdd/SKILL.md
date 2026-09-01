---
name: tdd
description: Develop behavior through small failing, passing, and refactoring test cycles. Use when implementing a change with tests, practicing test-driven development, or when behavior needs a precise executable contract.
---

# Test-Driven Development

Use the smallest useful cycle:

1. Write one test for observable behavior that does not yet work.
2. Run it and confirm it fails for the intended reason.
3. Implement the minimum behavior needed to pass.
4. Run the focused test, then the broader relevant suite.
5. Refactor while keeping the tests green.

Prefer tests at the highest stable seam that can verify the behavior. Avoid coupling tests to implementation details. Add edge cases when they represent distinct user-visible outcomes or failure modes.
