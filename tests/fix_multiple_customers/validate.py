"""Replace the sale workflow with its pinned test version and run it via act."""

import os
from pathlib import Path
import shutil
import subprocess

from scripts.lifecycle_opencode import expected_primary_models, validate_implementation_handoff, validate_observability


VALIDATION_COMMIT = "992714fce90ff9787f1f026d03a9f97da708c074"
IMPLEMENTATION_BRANCH = "e2e/fix-multiple-customers"
WORKFLOW = ".github/workflows/test-sale.yml"

workspace = Path(os.environ["TEST_WORKSPACE"])
artifacts = Path(os.environ["TEST_ARTIFACTS"])
repository = workspace / "tmp"
act = shutil.which("act")
if act is None:
    raise RuntimeError("act is not installed")

validate_observability(
    artifacts,
    expected_stages=("spec-orchestrator", "implementation"),
    expected_models=expected_primary_models(),
)
validate_implementation_handoff(artifacts, repository / ".scratch/fix-multiple-customers.md")

implemented_branch = subprocess.run(
    ["git", "branch", "--show-current"],
    cwd=repository,
    text=True,
    stdout=subprocess.PIPE,
    check=True,
).stdout.strip()
if implemented_branch != IMPLEMENTATION_BRANCH:
    raise AssertionError(
        f"implementation left guarded branch: {implemented_branch!r}"
    )

workflow = subprocess.run(
    ["git", "show", f"{VALIDATION_COMMIT}:{WORKFLOW}"],
    cwd=repository,
    stdout=subprocess.PIPE,
    check=True,
).stdout
(repository / WORKFLOW).write_bytes(workflow)

with (artifacts / "act.log").open("w") as output:
    subprocess.run(
        [
            act,
            "workflow_dispatch",
            "-W",
            WORKFLOW,
            "-j",
            "test",
            "-P",
            "odoo-17=localhost/odoo:17",
            "--pull=false",
            "--rm",
        ],
        cwd=repository,
        stdout=output,
        stderr=subprocess.STDOUT,
        check=True,
    )
