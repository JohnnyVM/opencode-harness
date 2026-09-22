"""Replace the sale workflow with its pinned test version and run it via act."""

import os
from pathlib import Path
import shutil
import subprocess

from scripts.lifecycle_opencode import validate_observability


VALIDATION_COMMIT = "229d0491bc3f3ea67e39eb02110e73ca6fdeb1a9"
START_COMMIT = "089f7e16cc6d53b5d26692dbee38a73e372ca3f4"
IMPLEMENTATION_BRANCH = "e2e/modify-buy-sale-command"
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
    expected_models=("openai/gpt-5.6-sol", "openai/gpt-5.6-terra"),
)

implemented_head = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    cwd=repository,
    text=True,
    stdout=subprocess.PIPE,
    check=True,
).stdout.strip()
if implemented_head == START_COMMIT:
    raise AssertionError("implementation did not create a commit")

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
