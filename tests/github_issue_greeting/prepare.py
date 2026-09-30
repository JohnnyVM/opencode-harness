"""Create an isolated repository for the local greeting specification."""

import os
from pathlib import Path
import subprocess


IMPLEMENTATION_BRANCH = "repro/issue-backed-basic-greeting"

workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
repository.mkdir()
subprocess.run(["git", "init", "--initial-branch", "main"], cwd=repository, check=True)
subprocess.run(["git", "config", "user.name", "Lifecycle Test"], cwd=repository, check=True)
subprocess.run(
    ["git", "config", "user.email", "lifecycle@example.test"], cwd=repository, check=True
)
(repository / "README.md").write_text("# Local architecture implementation fixture\n")
subprocess.run(["git", "add", "README.md"], cwd=repository, check=True)
subprocess.run(["git", "commit", "-m", "Add issue implementation baseline"], cwd=repository, check=True)
baseline = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    cwd=repository,
    text=True,
    stdout=subprocess.PIPE,
    check=True,
).stdout.strip()
(workspace / "baseline.txt").write_text(baseline)
subprocess.run(
    ["git", "switch", "--create", IMPLEMENTATION_BRANCH], cwd=repository, check=True
)
(repository / ".git" / "info" / "exclude").write_text(
    ".scratch/\n.agent-trace/\n__pycache__/\n"
)
(repository / ".scratch").mkdir()
(repository / ".scratch" / "greeting-specification.md").write_text(
    Path(__file__).with_name("specification.md").read_text()
)
