"""Clone connector-proyect at the pinned starting commit."""

import os
from pathlib import Path
import shutil
import subprocess


START_COMMIT = "20376ca2a63b5e447258fb9ca4cdc4a63c7593cb"

workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
gh = shutil.which("gh")
if not gh:
    raise RuntimeError("gh CLI is not installed")

subprocess.run(
    [gh, "repo", "clone", "git@github.com:Guadalsistema/connector-proyect.git", str(repository)],
    check=True,
)
subprocess.run(
    ["git", "switch", "--create", "e2e/brand-selection", START_COMMIT],
    cwd=repository,
    check=True,
)
with (repository / ".git" / "info" / "exclude").open("a") as stream:
    stream.write("\n.agent-trace/\n")
