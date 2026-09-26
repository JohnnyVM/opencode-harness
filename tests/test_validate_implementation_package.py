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

PACKAGE = """status: SPEC_APPROVED_BY_AGENT

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


class ValidatorTests(unittest.TestCase):
    def test_valid_package_and_read_only_cli(self):
        self.assertEqual(validator.validate(PACKAGE), [])
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], input=PACKAGE, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("VALID", result.stdout)

    def test_rejects_prose_and_missing_sections(self):
        errors = validator.validate("Please implement saved items")
        self.assertIn("requires exactly one valid status field", errors)
        self.assertIn("missing or empty section: Tickets and Dependencies", errors)

    def test_rejects_duplicate_status_and_placeholder(self):
        errors = validator.validate(PACKAGE + "\nstatus: SPEC_APPROVED_BY_USER\nTODO\n")
        self.assertIn("requires exactly one valid status field", errors)
        self.assertIn("contains a placeholder or unresolved TODO/TBD", errors)

    def test_rejects_invalid_ticket_graph_and_criteria(self):
        changed = PACKAGE.replace("Dependencies: None", "Dependencies: T2", 1)
        changed = changed.replace("Criteria: AC1", "Criteria: AC9", 1)
        errors = validator.validate(changed)
        self.assertTrue(any("cyclic ticket dependencies" in error for error in errors))
        self.assertIn("T1: unknown criterion AC9", errors)

    def test_rejects_missing_or_empty_approach(self):
        for replacement in ("", "- Approach: None\n", "- Approach: \n"):
            with self.subTest(replacement=replacement):
                changed = PACKAGE.replace(
                    "- Approach: Render saved items from existing storage in the public view.\n",
                    replacement,
                )
                self.assertTrue(
                    any("Approach" in error and error.startswith("T1:")
                        for error in validator.validate(changed))
                )

    def test_rejects_scope_without_paths_and_unassigned_criterion(self):
        changed = PACKAGE.replace("- Allowed: src/items", "- Allowed: None", 1)
        changed = changed.replace(
            "## Verification Commands", "- AC2: Saved items have labels.\n## Verification Commands"
        )
        errors = validator.validate(changed)
        self.assertIn("T1: Allowed requires concrete scope", errors)
        self.assertIn("unassigned criterion: AC2", errors)

    def test_rejects_incomplete_checks_and_blocking_unknowns(self):
        changed = PACKAGE.replace("- Working directory: .\n", "")
        changed = changed.replace("## Explicit Unknowns\nNone", "## Explicit Unknowns\nBlocking decision: storage format")
        errors = validator.validate(changed)
        self.assertTrue(any("Working directory" in error for error in errors))
        self.assertTrue(any("blocking requirements" in error for error in errors))

    def test_rejects_outdated_verification_section(self):
        changed = PACKAGE.replace("## Risks", "### Remote\nNot applicable: no checks\n## Risks")
        self.assertIn(
            "Verification Commands: unexpected section: Remote", validator.validate(changed)
        )

    def test_rejects_outdated_check_inside_local_section(self):
        changed = PACKAGE.replace("## Risks", "#### R1 — CI\n- Command: ci status\n## Risks")
        self.assertIn("Local: unexpected check: R1 — CI", validator.validate(changed))


if __name__ == "__main__":
    unittest.main()
