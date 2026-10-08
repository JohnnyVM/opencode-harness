import importlib.util
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
PACKAGE = f"""package-version: 2
status: ARCHITECTURE_READY
## Decision Summary
Recommendation and trade-offs.
## Repository Findings
Evidence from src/file.py.
## Architecture Candidates
### C1 — Extend existing module
- Structure: Existing module owns behavior.
### C2 — Add adapter
- Structure: Adapter owns behavior.
## Comparison and Recommendation
| Criterion | C1 — Extend | C2 — Adapter |
|---|---|---|
| Repository fit | Good | New seam |
Selected C1 because it reuses the existing seam.
## Proposed Design
### D1 — Keep behavior in module
- Decision: Extend existing implementation.
## Interfaces and Behavior
Existing interface is preserved.
## Implementation Plan
### T1 — Build
- Dependencies: None
- Allowed: src/file.py
- Forbidden: None
- Criteria: AC1
- Approach: Implement feature
- Outputs: Working feature.
## Testing Strategy
Reuse focused tests.
## Verification Matrix
### Local
#### L1 — Tests
- Command: python3 -m unittest
- Working directory: .
- Prerequisites: None
- Expected: Pass
## Requirements Traceability
| Criterion | Design decisions | Tickets | Verification |
|---|---|---|---|
| AC1 | D1 | T1 | L1 |
## Risks and Open Questions
### Risks
None
### Open questions
None
## Frozen Specification
<!-- BEGIN SPECIFICATION PACKAGE -->
{SPEC}
<!-- END SPECIFICATION PACKAGE -->
"""


class ArchitectureTests(unittest.TestCase):
    def test_valid_and_rejects_cycle_or_bad_embedding(self):
        self.assertEqual(validator.validate(PACKAGE, SPEC), [])
        self.assertEqual(validator.validate(PACKAGE), [])
        self.assertIn(
            "embedded specification differs from the supplied Specification Package",
            validator.validate(PACKAGE.replace("AC1: Works", "AC1: Changed"), SPEC),
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
            "missing or empty section: Decision Summary",
            validator.validate(PACKAGE.replace("## Decision Summary\nRecommendation and trade-offs.", "## Decision Summary")),
        )
        extra = PACKAGE.replace("## Risks", "- AC2: Also works\n## Risks")
        self.assertIn("unassigned criterion: AC2", validator.validate(extra))
        self.assertIn(
            "T1: Allowed requires concrete scope",
            validator.validate(PACKAGE.replace("- Allowed: src/file.py", "- Allowed: None")),
        )

    def test_rejects_v1_and_enforces_traceability_and_candidate_comparison(self):
        old_format = PACKAGE.replace("package-version: 2", "").replace("## Decision Summary", "## Architecture Summary")
        self.assertTrue(any("package-version: 2" in error for error in validator.validate(old_format)))
        self.assertIn("missing traceability row for AC1", validator.validate(
            PACKAGE.replace("| AC1 | D1 | T1 | L1 |", "| AC9 | D1 | T1 | L1 |")
        ))
        self.assertIn("Comparison and Recommendation must compare C2", validator.validate(
            PACKAGE.replace("| Criterion | C1 — Extend | C2 — Adapter |", "| Criterion | C1 — Extend | Other |")
        ))
        self.assertIn("AC1: T1 does not declare this criterion", validator.validate(
            PACKAGE.replace("- Criteria: AC1", "- Criteria: AC2")
        ))
        self.assertEqual(validator.validate(PACKAGE, SPEC), [])


if __name__ == "__main__":
    unittest.main()
