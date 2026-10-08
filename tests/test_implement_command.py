"""The command hook must validate both sources before handing text to the agent."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "opencode" / "plugins" / "implement.js"
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

RUN_HOOK = """
import { pathToFileURL } from "node:url";
const { default: plugin } = await import(pathToFileURL(process.argv[1]).href);
const hook = (await plugin({ directory: process.cwd() }))["command.execute.before"];
const parts = [{ type: "text", text: "placeholder" }];
try {
            await hook({ command: process.argv[3] || "implement", arguments: process.argv[2] }, { parts });
  process.stdout.write(JSON.stringify(parts));
} catch (error) {
  process.stderr.write(error.message);
  process.exitCode = 1;
}
"""


def issue_environment(directory, issue):
    env = os.environ.copy()
    bin_dir = directory / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "assert sys.argv[1:] == ['issue', 'view', '42', '--repo', 'acme/widget', '--json', 'body,state']\n"
        "if os.environ.get('FAKE_ISSUE_ERROR'):\n"
        "    print(os.environ['FAKE_ISSUE_ERROR'], file=sys.stderr)\n"
        "    raise SystemExit(1)\n"
        "print(json.dumps({'body': os.environ['FAKE_ISSUE_BODY'], "
        "'state': os.environ['FAKE_ISSUE_STATE']}))\n"
    )
    gh.chmod(0o755)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FAKE_ISSUE_BODY"] = issue.get("body", "")
    env["FAKE_ISSUE_STATE"] = issue.get("state", "OPEN")
    env["FAKE_ISSUE_ERROR"] = issue.get("error", "")
    return env


def run_hook(source, directory, *, issue=None, command="implement"):
    env = issue_environment(directory, issue) if issue is not None else os.environ.copy()
    return subprocess.run(
        ["node", "--input-type=module", "-e", RUN_HOOK, str(PLUGIN), source, command],
        cwd=directory, env=env, text=True, capture_output=True, check=False,
    )


class ImplementCommandTests(unittest.TestCase):
    def test_opencode_plugin_has_only_one_entrypoint(self):
        result = subprocess.run(
            ["node", "--input-type=module", "-e",
             "import { pathToFileURL } from 'node:url'; "
             "const plugin = await import(pathToFileURL(process.argv[1]).href); "
             "process.stdout.write(JSON.stringify(Object.keys(plugin)));", str(PLUGIN)],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ["default"])

    def test_file_package_replaces_prompt_exactly(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = "package with spaces;$(false).md"
            (directory / source).write_text(PACKAGE)
            result = run_hook(source, directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), [{"type": "text", "text": PACKAGE}])

    def test_retired_v1_package_is_rejected_with_regeneration_guidance(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "old-architecture.md").write_text(PACKAGE.replace("package-version: 2", "package-version: 1"))
            result = run_hook("old-architecture.md", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("version 1 packages must be regenerated", result.stderr)
            self.assertEqual(result.stdout, "")

    def test_github_issue_package_replaces_prompt_exactly(self):
        clarification = (
            "CLOSED_ISSUE_CLARIFICATION_REQUIRED: GitHub issue acme/widget#42 is closed. "
            "Ask the user whether to proceed with this closed issue or stop. Do not begin "
            "implementation until the user explicitly confirms."
        )
        for state, expected in (
            ("OPEN", [{"type": "text", "text": PACKAGE}]),
            ("CLOSED", [{"type": "text", "text": clarification},
                        {"type": "text", "text": PACKAGE}]),
        ):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temp:
                issue = {"body": PACKAGE, "state": state}
                result = run_hook("acme/widget#42", Path(temp), issue=issue)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), expected)

    def test_github_issue_url_replaces_prompt_exactly(self):
        for source in (
            "https://github.com/acme/widget/issues/42",
            "https://github.com/acme/widget/issues/42/",
        ):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temp:
                result = run_hook(source, Path(temp), issue={"body": PACKAGE})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), [{"type": "text", "text": PACKAGE}])

    def test_invalid_issue_body_stops_handoff(self):
        for issue, expected in (
            ({"body": "Implement feature"}, "INVALID:"),
            ({"error": "could not resolve to an issue"}, "BLOCKED_SPEC"),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                result = run_hook("acme/widget#42", Path(temp), issue=issue)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)
                self.assertEqual(result.stdout, "")

    @unittest.skipUnless(shutil.which("opencode"), "OpenCode CLI not installed")
    def test_opencode_rejects_invalid_github_issue_before_agent_run(self):
        for issue, expected in (
            ({"body": "Implement feature"}, "INVALID:"),
            ({"error": "could not resolve to an issue"}, "BLOCKED_SPEC"),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                env = issue_environment(directory, issue)
                env["OPENCODE_CONFIG_DIR"] = str(ROOT / "opencode")
                env["OPENCODE_CONFIG_CONTENT"] = '{"mcp":{"playwright":{"enabled":false}}}'
                env["OPENCODE_DISABLE_MODELS_FETCH"] = "1"
                env["OPENCODE_DISABLE_LSP_DOWNLOAD"] = "1"
                result = subprocess.run(
                    ["opencode", "run", "--print-logs", "--log-level", "ERROR", "--command",
                      "implement", "--dir", str(directory), "--format", "json", "acme/widget#42"],
                    env=env, cwd=directory, text=True, capture_output=True, check=False, timeout=30,
                )
                self.assertIn(expected, result.stderr)
                events = [
                    json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")
                ]
                self.assertFalse(any(event["type"] == "step_start" for event in events))

    def test_nonarchitecture_files_stop_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for source, content in (("prose.md", "Implement feature"), ("specification.md", SPEC)):
                with self.subTest(source=source):
                    (directory / source).write_text(content)
                    result = run_hook(source, directory)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Invalid Architecture Package", result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_missing_source_stops_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for source, expected in (("", "Usage:"), ("missing.md", "Cannot read package file")):
                with self.subTest(source=source):
                    result = run_hook(source, directory)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected, result.stderr)
                    self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
