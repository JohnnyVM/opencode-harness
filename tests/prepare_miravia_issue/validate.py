"""Require a completed implementation and working real-Odoo foundation."""

import json
import os
from pathlib import Path
import re
import subprocess

from scripts.lifecycle_opencode import (
    expected_primary_models,
    validate_implementation_handoff,
    validate_implementation_report,
    validate_observability,
)


BASELINE = "0130a245d35846014372db652acf9d809ac81d0d"
BRANCH = "feature/preparation-miravia"

workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
artifacts = Path(os.environ["TEST_ARTIFACTS"])
package = workspace / "issue-package.md"

validate_observability(
    artifacts,
    expected_stages=("implementation",),
    expected_models=(expected_primary_models()[1],),
)
validate_implementation_handoff(artifacts, package)
validate_implementation_report(artifacts, package)

sessions = [
    json.loads(path.read_text())
    for path in (artifacts / "implementation" / "sessions").glob("*.json")
]
orchestrators = [
    message
    for session in sessions
    for message in session.get("messages", [])
    if message.get("info", {}).get("role") == "assistant"
    and message["info"].get("agent") == "implementation-orchestrator"
]
if not orchestrators:
    raise AssertionError("missing implementation-orchestrator response")
report = "\n".join(
    part.get("text", "") for part in orchestrators[-1].get("parts", [])
    if part.get("type") == "text"
)
(artifacts / "implementation-report.md").write_text(report)
outcome = report.split("## Outcome and Stopping Point", 1)[-1].split("## Ticket Ledger", 1)[0]
if not re.search(r"\bDONE\b", outcome) or re.search(r"\bBLOCKED_\w+\b", outcome):
    raise AssertionError(f"implementation did not reach DONE:\n{outcome}")
ledger = report.split("## Ticket Ledger", 1)[1].split("## Verification", 1)[0]
if len(re.findall(r"^- T\d+: completed\b", ledger, re.MULTILINE)) != 9:
    raise AssertionError(f"not all nine issue tickets completed:\n{ledger}")

for agent, evidence in (
    ("tester", r"status:\s*PASS\b"),
    ("code-reviewer", r"Verdict:\s*APPROVED\b"),
    ("cleaner", r"\bPASS\b"),
):
    replies = [
        "\n".join(part.get("text", "") for part in message.get("parts", [])
                  if part.get("type") == "text")
        for session in sessions
        for message in session.get("messages", [])
        if message.get("info", {}).get("role") == "assistant"
        and message["info"].get("agent") == agent
    ]
    if not replies or not re.search(evidence, replies[-1], re.IGNORECASE):
        raise AssertionError(f"missing final {agent} approval; replies: {replies[-1:]}")

def git(*args):
    return subprocess.run(
        ["git", *args], cwd=repository, text=True, capture_output=True, check=True
    ).stdout.strip()


if git("branch", "--show-current") != BRANCH:
    raise AssertionError("implementation left the admitted branch")
if git("rev-parse", "main") != BASELINE:
    raise AssertionError("implementation changed the protected baseline")
if git("status", "--porcelain"):
    raise AssertionError("implementation left uncommitted changes")
if git("rev-list", "--count", "main..HEAD") == "0":
    raise AssertionError("implementation did not commit the candidate")
subprocess.run(["git", "diff", "--check", "main...HEAD"], cwd=repository, check=True)

# Independently rerun the checks that caught the prior incomplete T7/T9 work.
for command, label in (
    (["go", "test", "-tags=odoo_e2e", "./internal/testutil/odoo",
      "-run", "^TestRealOdooProductLifecycle$", "-v"], "odoo-smoke"),
    (["bash", "scripts/test.sh"], "full-test-runner"),
):
    with (artifacts / f"{label}.log").open("w") as output:
        subprocess.run(command, cwd=repository, stdout=output,
                       stderr=subprocess.STDOUT, check=True)
