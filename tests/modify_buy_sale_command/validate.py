"""Replace the sale workflow with its pinned test version and run it via act."""

import os
from pathlib import Path
import shutil
import subprocess

from scripts.lifecycle_opencode import (
    expected_primary_models,
    validate_architect_handoff,
    validate_coder_assignments,
    validate_implementation_handoff,
    validate_observability,
)


VALIDATION_COMMIT = "229d0491bc3f3ea67e39eb02110e73ca6fdeb1a9"
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
    expected_stages=("specification", "architecture", "implementation"),
    expected_models=expected_primary_models(),
)
specification = repository / ".scratch/modify-buy-sale-command-specification.md"
architecture = repository / ".scratch/modify-buy-sale-command-architecture.md"
if not architecture.is_file():
    raise AssertionError("architect did not create the architecture file")
validate_architect_handoff(artifacts, specification, architecture)
validate_implementation_handoff(artifacts, architecture)
validate_coder_assignments(artifacts)

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
