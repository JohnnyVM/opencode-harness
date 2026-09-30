import importlib.util
import hashlib
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "opencode/scripts/validate_architecture_package.py"
spec = importlib.util.spec_from_file_location("architecture_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

SPEC = """status: SPEC_APPROVED_BY_USER
## Problem Statement
P
## Solution
S
## User Stories
U
## Product Decisions and Constraints
D
## Testing Decisions
T
## Acceptance Criteria
- AC1: Works
## Risks
None
## Explicit Unknowns
None
## Out of Scope
None"""
PACKAGE = f"""status: ARCHITECTURE_READY
specification-bytes: {len(SPEC.encode("utf8"))}
specification-sha256: {hashlib.sha256(SPEC.encode("utf8")).hexdigest()}
<!-- BEGIN SPECIFICATION PACKAGE -->
{SPEC}
<!-- END SPECIFICATION PACKAGE -->
## Architecture Summary
Summary
## Usage and Interface Sketch
Sketch
## Structural Decisions
Decisions
## Implementation Decisions
Decisions
## Testing Strategy
Tests
## Tickets and Dependencies
### T1 — Build
- Dependencies: None
- Allowed: src/file.py
- Forbidden: None
- Criteria: AC1
- Approach: Implement feature
## Verification Matrix
### Local
#### L1 — Tests
- Command: python3 -m unittest
- Working directory: .
- Prerequisites: None
- Expected: Pass
## Architecture Risks
None
## Architecture Unknowns
None
"""


class ArchitectureTests(unittest.TestCase):
    def test_valid_and_rejects_cycle_or_bad_embedding(self):
        self.assertEqual(validator.validate(PACKAGE, SPEC), [])
        self.assertIn(
            "embedded specification differs from the supplied Specification Package",
            validator.validate(PACKAGE.replace("AC1: Works", "AC1: Changed"), SPEC),
        )
        self.assertIn(
            "embedded specification does not match its byte count and SHA-256",
            validator.validate(PACKAGE.replace("AC1: Works", "AC1: Changed")),
        )
        self.assertTrue(any("cyclic" in e.lower() for e in validator.validate(PACKAGE.replace("Dependencies: None", "Dependencies: T1"))))
        self.assertIn(
            "T1: unknown criterion AC1",
            validator.validate(PACKAGE.replace("AC1: Works", "AC2: Works")),
        )
        self.assertTrue(any("marker" in e.lower() for e in validator.validate(PACKAGE.replace("<!-- END SPECIFICATION PACKAGE -->", ""))))

    def test_allows_markdown_links_arrays_and_shell_classes(self):
        additions = "\nSee [the docs](https://example.com), list[str], and file[0-9]."
        self.assertEqual(validator.validate(PACKAGE.replace("Summary", "Summary" + additions, 1)), [])
        self.assertTrue(any("placeholder" in e for e in validator.validate(
            PACKAGE.replace("Summary", "{{Chosen shape}}", 1)
        )))

    def test_rejects_empty_section_unassigned_criterion_and_nonconcrete_scope(self):
        self.assertIn(
            "missing or empty section: Architecture Summary",
            validator.validate(PACKAGE.replace("## Architecture Summary\nSummary", "## Architecture Summary")),
        )
        extra = PACKAGE.replace("## Risks", "- AC2: Also works\n## Risks")
        self.assertIn("unassigned criterion: AC2", validator.validate(extra))
        self.assertIn(
            "T1: Allowed requires concrete scope",
            validator.validate(PACKAGE.replace("- Allowed: src/file.py", "- Allowed: None")),
        )


if __name__ == "__main__":
    unittest.main()
