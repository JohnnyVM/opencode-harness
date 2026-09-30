import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "opencode/scripts/validate_coder_assignment.py"
spec = importlib.util.spec_from_file_location("assignment_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

PACKAGE = """status: ASSIGNMENT_READY
## Objective
Build it
## Relevant Specification
Specification content
## Relevant Architecture
Architecture content
## Ticket Scope
- Ticket: T1
- Dependencies: None
- Allowed: src/file.py
- Forbidden: None
- Approach: Build feature
## Acceptance Criteria
- AC1: Works
## Test Strategy
Test it
## Focused Checks
### C1 — Unit test
- Command: `python3 -m unittest`
- Working directory: .
- Prerequisites: None
- Expected: Zero exit status
## Repository Snapshot
- Branch: main
- Baseline: abc
- Expected HEAD: abc
- Expected candidate: None
- Additional allowed scope: None
## Dependency Outputs
None
## Test-First Evidence
None
"""


class AssignmentTests(unittest.TestCase):
    def test_valid_and_rejects_missing_snapshot_or_placeholder(self):
        self.assertEqual(validator.validate(PACKAGE), [])
        self.assertTrue(any("Expected HEAD" in e for e in validator.validate(PACKAGE.replace("- Expected HEAD: abc\n", ""))))
        self.assertTrue(any("placeholder" in e for e in validator.validate(PACKAGE.replace("Build it", "TODO"))))
        self.assertTrue(any("status" in e for e in validator.validate(PACKAGE.replace("ASSIGNMENT_READY", "READY"))))

    def test_allows_bracket_syntax_and_rejects_template_markers(self):
        decorated = PACKAGE.replace("Build it", "Build list[str]; see [docs](https://example.com)")
        self.assertEqual(validator.validate(decorated), [])
        self.assertTrue(any("placeholder" in e for e in validator.validate(
            PACKAGE.replace("Build it", "{{Ticket ID and objective}}")
        )))


if __name__ == "__main__":
    unittest.main()
