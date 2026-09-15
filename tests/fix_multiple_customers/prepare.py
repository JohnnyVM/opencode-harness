"""Clone GuadalBot at the pinned starting commit."""

import os
from pathlib import Path
import shutil
import subprocess


START_COMMIT = "28934acb77f75d47e9b4b0c5058294cd3db6a513"

workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
gh = shutil.which("gh")
if gh is None:
    raise RuntimeError("gh CLI is not installed")

subprocess.run(
    [gh, "repo", "clone", "Guadalsistema/guadalbot", str(repository)],
    check=True,
)
subprocess.run(
    ["git", "checkout", "--detach", START_COMMIT],
    cwd=repository,
    check=True,
)
