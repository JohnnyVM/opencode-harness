"""Create an isolated repository matching the GitHub issue package."""

import json
import os
from pathlib import Path
import subprocess


ISSUE_REPOSITORY = "JohnnyVM/opencode-harness"
ISSUE_NUMBER = "38"
IMPLEMENTATION_BRANCH = "repro/issue-backed-basic-greeting"

workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
repository.mkdir()
subprocess.run(["git", "init", "--initial-branch", "main"], cwd=repository, check=True)
subprocess.run(["git", "config", "user.name", "Lifecycle Test"], cwd=repository, check=True)
subprocess.run(
    ["git", "config", "user.email", "lifecycle@example.test"], cwd=repository, check=True
)
(repository / "README.md").write_text("# GitHub issue implementation fixture\n")
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
    ["git", "remote", "add", "origin", f"https://github.com/{ISSUE_REPOSITORY}.git"],
    cwd=repository,
    check=True,
)
subprocess.run(
    ["git", "switch", "--create", IMPLEMENTATION_BRANCH], cwd=repository, check=True
)
(repository / ".git" / "info" / "exclude").write_text(
    ".scratch/\n.agent-trace/\n__pycache__/\n"
)

response = subprocess.run(
    [
        "gh",
        "issue",
        "view",
        ISSUE_NUMBER,
        "--repo",
        ISSUE_REPOSITORY,
        "--json",
        "body",
    ],
    text=True,
    stdout=subprocess.PIPE,
    check=True,
)
(workspace / "issue-package.md").write_text(json.loads(response.stdout)["body"])
(workspace / "issue-reference.txt").write_text(f"{ISSUE_REPOSITORY}#{ISSUE_NUMBER}")
