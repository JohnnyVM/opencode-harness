status: SPEC_APPROVED_BY_AGENT

## Problem Statement
The lifecycle harness needs a small isolated example that exercises the complete architecture and implementation workflow without a large external specification.

## Solution
Add a minimal Python greeting example under `examples/basic_greeting`. It exposes `greet(name)`, returns exactly `Hello, <name>!`, and includes a focused unittest.

## User Stories
1. As a workflow maintainer, I want a tiny implementation fixture, so that I can reproduce the complete handoff safely.
2. As an example user, I want a friendly greeting, so that the behavior is immediately understandable.

## Product Decisions and Constraints
- Keep the example under `examples/basic_greeting` and independent of `tests/basic_greeting`.
- Interpolate the supplied name verbatim.
- Use only the Python standard library.
- Do not modify lifecycle harness or OpenCode configuration files.

## Testing Decisions
- Add a focused unittest beside the example.
- Assert that `greet("Ada")` returns exactly `Hello, Ada!`.

## Acceptance Criteria
- AC1: `examples/basic_greeting/greeting.py` defines `greet(name)`.
- AC2: `greet("Ada")` returns exactly `Hello, Ada!`.
- AC3: The focused unittest passes without third-party dependencies.

## Risks
- This fixture intentionally exercises only deterministic behavior.

## Explicit Unknowns
None

## Out of Scope
- Changing lifecycle harness, OpenCode configuration, or agent contracts.
- Adding external dependencies or additional greeting formats.
