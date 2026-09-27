"""Pin connector-proyect to the approved issue #10 baseline."""

import json
import os
from pathlib import Path
import shutil
import subprocess


REPOSITORY = "Guadalsistema/connector-proyect"
BASELINE = "0130a245d35846014372db652acf9d809ac81d0d"
BRANCH = "feature/preparation-miravia"

workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
gh = shutil.which("gh")
if gh is None:
    raise RuntimeError("gh CLI is not installed")

for command, expected in (
    (["go", "version"], "go1.25.5"),
    (["protoc", "--version"], "31.1"),
    (["clang-format", "--version"], "version 18"),
    (["protoc-gen-go", "--version"], "v1.36.6"),
    (["protoc-gen-go-grpc", "--version"], "1.5.1"),
):
    output = subprocess.run(command, text=True, capture_output=True, check=True).stdout
    if expected not in output:
        raise RuntimeError(f"expected {expected} from {' '.join(command)}, got {output!r}")
rootless = subprocess.run(
    ["podman", "info", "--format", "{{.Host.Security.Rootless}}"],
    text=True, capture_output=True, check=True,
).stdout.strip()
if rootless != "true":
    raise RuntimeError("rootless Podman is required")
for image in ("docker.io/library/postgres:17", "docker.io/library/odoo:17"):
    subprocess.run(["podman", "image", "exists", image], check=True)

subprocess.run([gh, "repo", "clone", REPOSITORY, str(repository)], check=True)
subprocess.run(["git", "switch", "--detach", BASELINE], cwd=repository, check=True)
# The local protected branch is pinned even when the remote main has advanced.
subprocess.run(["git", "branch", "--force", "main", BASELINE], cwd=repository, check=True)
subprocess.run(["git", "switch", "--create", BRANCH, BASELINE], cwd=repository, check=True)
subprocess.run(["git", "config", "user.name", "Lifecycle Test"], cwd=repository, check=True)
subprocess.run(
    ["git", "config", "user.email", "lifecycle@example.test"], cwd=repository, check=True
)
(repository / ".git" / "info" / "exclude").write_text(
    ".scratch/\n.agent-trace/\n__pycache__/\n"
)

response = subprocess.run(
    [gh, "issue", "view", "10", "--repo", REPOSITORY, "--json", "body,state"],
    text=True, capture_output=True, check=True,
)
issue = json.loads(response.stdout)
if issue["state"] != "OPEN":
    raise AssertionError("issue #10 must be open for unattended implementation")
(workspace / "issue-package.md").write_text(issue["body"])
