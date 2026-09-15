"""Replace the sale workflow with its pinned test version and run it via act."""

import os
from pathlib import Path
import shutil
import subprocess


VALIDATION_COMMIT = "229d0491bc3f3ea67e39eb02110e73ca6fdeb1a9"
WORKFLOW = ".github/workflows/test-sale.yml"

workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
act = shutil.which("act")
if not act:
    raise RuntimeError("act is not installed")

workflow = subprocess.run(
    ["git", "show", f"{VALIDATION_COMMIT}:{WORKFLOW}"],
    cwd=repository,
    stdout=subprocess.PIPE,
    check=True,
).stdout
(repository / WORKFLOW).write_bytes(workflow)

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
    check=True,
)
