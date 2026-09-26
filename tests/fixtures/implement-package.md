status: SPEC_APPROVED_BY_AGENT

## Problem Statement
Users cannot see saved items.
## Solution
Display saved items.
## User Stories
1. As a user, I want saved items displayed so that I can find them.
## Implementation Decisions
- Use existing storage.
## Testing Decisions
- Test the public saved-items view.
## Tickets and Dependencies
### T1 — Display items
- Dependencies: None
- Allowed: src/items
- Forbidden: src/auth
- Criteria: AC1
- Approach: Render saved items from existing storage in the public view.
## Acceptance Criteria
- AC1: Saved items are displayed on the view.
## Verification Commands
### Local
#### L1 — Run view tests
- Command: `python3 -m unittest tests.items`
- Working directory: .
- Prerequisites: None
- Expected: Zero exit status
## Risks
None identified
## Explicit Unknowns
None
## Out of Scope
Item editing
