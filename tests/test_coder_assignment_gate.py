import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "opencode/plugins/implement.js"
ASSIGNMENT = """status: ASSIGNMENT_READY
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
RUN = """
import {pathToFileURL} from 'node:url';
const {default: plugin}=await import(pathToFileURL(process.argv[1]).href);
const hook=(await plugin({directory:process.cwd()}))['tool.execute.before'];
try { await hook({tool:'task'}, {args:{subagent_type:process.argv[2], prompt:process.argv[3]}}); process.stdout.write('accepted'); }
catch(e) { process.stderr.write(e.message); process.exitCode=1; }
"""


def invoke(agent, prompt):
    return subprocess.run(["node", "--input-type=module", "-e", RUN, str(PLUGIN), agent, prompt],
                          cwd=ROOT, text=True, capture_output=True, check=False)


class CoderAssignmentGateTests(unittest.TestCase):
    def test_valid_assignment_allowed_and_invalid_refused_for_both_coders(self):
        for coder in ("coder-light", "coder-heavy"):
            good = invoke(coder, ASSIGNMENT)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(good.stdout, "accepted")
            bad = invoke(coder, "status: ASSIGNMENT_READY\nTODO")
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("Invalid coder assignment", bad.stderr)

    def test_non_coder_tasks_are_not_gated(self):
        result = invoke("architect", "not an assignment")
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
