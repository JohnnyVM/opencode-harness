"""Verify the GitHub issue handoff and its isolated implementation."""

import os
from pathlib import Path
import subprocess
import unittest

from scripts.lifecycle_opencode import (
    expected_primary_models,
    validate_implementation_handoff,
    validate_observability,
)


IMPLEMENTATION_BRANCH = "repro/issue-backed-basic-greeting"

workspace = Path(os.environ["TEST_WORKSPACE"])
artifacts = Path(os.environ["TEST_ARTIFACTS"])
repository = workspace / "tmp"

validate_observability(
    artifacts,
    expected_stages=("implementation",),
    expected_models=(expected_primary_models()[1],),
)
validate_implementation_handoff(artifacts, workspace / "issue-package.md")

branch = subprocess.run(
    ["git", "branch", "--show-current"],
    cwd=repository,
    text=True,
    stdout=subprocess.PIPE,
    check=True,
).stdout.strip()
if branch != IMPLEMENTATION_BRANCH:
    raise AssertionError(f"implementation left guarded branch: {branch!r}")

baseline = subprocess.run(
    ["git", "rev-parse", "main"],
    cwd=repository,
    text=True,
    stdout=subprocess.PIPE,
    check=True,
).stdout.strip()
if baseline != (workspace / "baseline.txt").read_text():
    raise AssertionError("implementation changed the default branch")

status = subprocess.run(
    ["git", "status", "--porcelain"],
    cwd=repository,
    text=True,
    stdout=subprocess.PIPE,
    check=True,
).stdout
if status:
    raise AssertionError(f"implementation left a dirty worktree:\n{status}")

subprocess.run(["git", "diff", "--check", "main...HEAD"], cwd=repository, check=True)
subprocess.run(
    [
        "python3",
        "-m",
        "unittest",
        "discover",
        "-s",
        "examples/basic_greeting",
        "-p",
        "test_*.py",
        "-v",
    ],
    cwd=repository,
    check=True,
)

example = repository / "examples" / "basic_greeting"
suite = unittest.defaultTestLoader.discover(str(example), pattern="test_*.py")
if suite.countTestCases() < 1:
    raise AssertionError("focused greeting unittest was not discovered")

subprocess.run(
    [
        "python3",
        "-c",
        "from greeting import greet; assert greet('Ada') == 'Hello, Ada!'",
    ],
    cwd=example,
    check=True,
)
