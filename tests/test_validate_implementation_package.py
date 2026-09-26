"""Contract examples and admission failures for the read-only package validator."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "opencode" / "scripts" / "validate_implementation_package.py"
spec = importlib.util.spec_from_file_location("package_validator", SCRIPT)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

# Test package with a test-first ticket and dependent implementation ticket
PACKAGE_WITH_TEST_FIRST_TICKET = """status: SPEC_APPROVED_BY_AGENT

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
### T2 — Verify view
- Dependencies: T1
- Allowed: tests/items
- Forbidden: src/auth
- Criteria: AC1
- Approach: Add a view test exercising the saved-items rendering.
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
"""

# Test package with a test-first ticket that includes the required red plan/prerequisite
PACKAGE_WITH_RED_PLAN = """status: SPEC_APPROVED_BY_AGENT

## Problem Statement
Implement authentication flow.
## Solution
Add login and logout functionality.
## User Stories
1. As a user, I want to log in so that I can access protected resources.
2. As a user, I want to log out so that my session is secure.
## Implementation Decisions
- Use JWT tokens for session management
- Implement password hashing
## Testing Decisions
- Test both successful and failed authentication flows
- Test session invalidation on logout
## Tickets and Dependencies
### T1 — Implement login endpoint
- Dependencies: None
- Allowed: src/auth/login.py
- Forbidden: None
- Criteria: AC1
- Approach: Create login endpoint that validates credentials and issues JWT token.
### T2 — Add login test
- Dependencies: T1
- Allowed: tests/auth/test_login.py
- Forbidden: None
- Criteria: AC1
- Approach: Add test that expects a red assertion for login endpoint before implementation.
  - Scenario: User attempts to login with invalid credentials
  - Location: tests/auth/test_login.py
  - Command: python3 -m unittest tests.auth.test_login.LoginTestCase.test_invalid_credentials
  - Expected preimplementation failure: AssertionError due to unimplemented endpoint
### T3 — Implement logout
- Dependencies: T1
- Allowed: src/auth/logout.py
- Forbidden: None
- Criteria: AC2
- Approach: Create logout endpoint that invalidates the JWT token.
## Acceptance Criteria
- AC1: Users can log in with valid credentials and receive a JWT token
- AC2: Users can log out and sessions are invalidated
## Verification Commands
### Local
#### L1 — Run auth tests
- Command: `python3 -m unittest tests.auth`
- Working directory: .
- Prerequisites: None
- Expected: Zero exit status
## Risks
None identified
## Explicit Unknowns
None
## Out of Scope
Password reset functionality
"""

# Alias for backward compatibility with test_implement_command.py
PACKAGE = PACKAGE_WITH_TEST_FIRST_TICKET

class ValidatorTests(unittest.TestCase):
    def test_valid_package_and_read_only_cli(self):
        self.assertEqual(validator.validate(PACKAGE_WITH_TEST_FIRST_TICKET), [])
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], input=PACKAGE_WITH_TEST_FIRST_TICKET, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("VALID", result.stdout)

    def test_valid_package_with_red_plan(self):
        """Test that packages with red plan/prerequisite information validate correctly."""
        self.assertEqual(validator.validate(PACKAGE_WITH_RED_PLAN), [])
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], input=PACKAGE_WITH_RED_PLAN, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("VALID", result.stdout)

    def test_rejects_prose_and_missing_sections(self):
        errors = validator.validate("Please implement saved items")
        self.assertIn("requires exactly one valid status field", errors)
        self.assertIn("missing or empty section: Tickets and Dependencies", errors)

    def test_rejects_duplicate_status_and_placeholder(self):
        errors = validator.validate(PACKAGE_WITH_TEST_FIRST_TICKET + "\nstatus: SPEC_APPROVED_BY_USER\nTODO\n")
        self.assertIn("requires exactly one valid status field", errors)
        self.assertIn("contains a placeholder or unresolved TODO/TBD", errors)

    def test_rejects_invalid_ticket_graph_and_criteria(self):
        changed = PACKAGE_WITH_TEST_FIRST_TICKET.replace("Dependencies: None", "Dependencies: T2", 1)
        changed = changed.replace("Criteria: AC1", "Criteria: AC9", 1)
        errors = validator.validate(changed)
        self.assertTrue(any("cyclic ticket dependencies" in error for error in errors))
        self.assertIn("T1: unknown criterion AC9", errors)

    def test_rejects_missing_or_empty_approach(self):
        for replacement in ("", "- Approach: None\n", "- Approach: \n"):
            with self.subTest(replacement=replacement):
                changed = PACKAGE_WITH_TEST_FIRST_TICKET.replace(
                    "- Approach: Render saved items from existing storage in the public view.\n",
                    replacement,
                )
                self.assertTrue(
                    any("Approach" in error and error.startswith("T1:")
                        for error in validator.validate(changed))
                )

    def test_rejects_scope_without_paths_and_unassigned_criterion(self):
        changed = PACKAGE_WITH_TEST_FIRST_TICKET.replace("- Allowed: src/items", "- Allowed: None", 1)
        changed = changed.replace(
            "## Verification Commands", "- AC2: Saved items have labels.\n## Verification Commands"
        )
        errors = validator.validate(changed)
        self.assertIn("T1: Allowed requires concrete scope", errors)
        self.assertIn("unassigned criterion: AC2", errors)

    def test_rejects_incomplete_checks_and_blocking_unknowns(self):
        changed = PACKAGE_WITH_TEST_FIRST_TICKET.replace("- Working directory: .\n", "")
        changed = changed.replace("## Explicit Unknowns\nNone", "## Explicit Unknowns\nBlocking decision: storage format")
        errors = validator.validate(changed)
        self.assertTrue(any("Working directory" in error for error in errors))
        self.assertTrue(any("blocking requirements" in error for error in errors))

    def test_rejects_outdated_verification_section(self):
        changed = PACKAGE_WITH_TEST_FIRST_TICKET.replace("## Risks", "### Remote\nNot applicable: no checks\n## Risks")
        self.assertIn(
            "Verification Commands: unexpected section: Remote", validator.validate(changed)
        )

    def test_rejects_outdated_check_inside_local_section(self):
        changed = PACKAGE_WITH_TEST_FIRST_TICKET.replace("## Risks", "#### R1 — CI\n- Command: ci status\n## Risks")
        self.assertIn("Local: unexpected check: R1 — CI", validator.validate(changed))


if __name__ == "__main__":
    unittest.main()