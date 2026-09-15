"""Clone GuadalBot at the pinned starting commit."""

import os
from pathlib import Path
import shutil
import subprocess


START_COMMIT = "089f7e16cc6d53b5d26692dbee38a73e372ca3f4"

workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
gh = shutil.which("gh")
if not gh:
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
