import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "opencode/scripts/validate_specification_package.py"
spec = importlib.util.spec_from_file_location("spec_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

PACKAGE = """status: SPEC_APPROVED_BY_AGENT
## Problem Statement
Problem
## Solution
Solution
## User Stories
Story
## Product Decisions and Constraints
Decision
## Testing Decisions
Test
## Acceptance Criteria
- AC1: Observable result
## Risks
None
## Explicit Unknowns
None
## Out of Scope
None
"""


class SpecificationTests(unittest.TestCase):
    def test_valid_and_rejects_invalid_status_unknown_and_duplicate_criteria(self):
        self.assertEqual(validator.validate(PACKAGE), [])
        self.assertTrue(any("status" in e for e in validator.validate(PACKAGE.replace("SPEC_APPROVED_BY_AGENT", "READY"))))
        self.assertTrue(any("blocking" in e.lower() for e in validator.validate(PACKAGE.replace("## Explicit Unknowns\nNone", "## Explicit Unknowns\nBlocking choice"))))
        self.assertTrue(any("duplicate criterion" in e for e in validator.validate(PACKAGE.replace("## Risks", "- AC1: duplicate\n## Risks"))))
        self.assertTrue(any("placeholder" in e for e in validator.validate(PACKAGE.replace("Problem", "TBD"))))

    def test_rejects_empty_and_unexpected_sections(self):
        self.assertIn(
            "missing or empty section: Solution",
            validator.validate(PACKAGE.replace("## Solution\nSolution", "## Solution")),
        )
        self.assertIn(
            "unexpected section: Implementation Decisions",
            validator.validate(PACKAGE + "\n## Implementation Decisions\nNot allowed\n"),
        )

    def test_allows_bracket_syntax_and_rejects_template_markers(self):
        decorated = PACKAGE.replace("\nProblem\n", "\nSee [the docs](https://example.com) and list[str]\n")
        self.assertEqual(validator.validate(decorated), [])
        self.assertTrue(any("placeholder" in e for e in validator.validate(
            PACKAGE.replace("Problem", "{{User-facing problem}}")
        )))


if __name__ == "__main__":
    unittest.main()
