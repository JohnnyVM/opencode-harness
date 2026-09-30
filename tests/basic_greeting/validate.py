"""Verify the handoff produced the requested behavior and its focused test."""

import os
from pathlib import Path
import subprocess

from scripts.lifecycle_opencode import (
    expected_primary_models,
    validate_architect_handoff,
    validate_coder_assignments,
    validate_implementation_handoff,
    validate_implementation_report,
    validate_observability,
)


workspace = Path(os.environ["TEST_WORKSPACE"])
artifacts = Path(os.environ["TEST_ARTIFACTS"])
repository = workspace / "tmp"

validate_observability(
    artifacts,
    expected_stages=("specification", "architecture", "implementation"),
    expected_models=expected_primary_models(),
)
specification = repository / ".scratch/basic-greeting-specification.md"
architecture = repository / ".scratch/basic-greeting-architecture.md"
if not architecture.is_file():
    raise AssertionError("architect did not create the architecture file")
validate_architect_handoff(artifacts, specification, architecture)
validate_implementation_handoff(artifacts, architecture)
validate_coder_assignments(artifacts)
validate_implementation_report(artifacts, architecture, expected_status="DONE")

branch = subprocess.run(
    ["git", "branch", "--show-current"],
    cwd=repository,
    text=True,
    stdout=subprocess.PIPE,
    check=True,
).stdout.strip()
if branch != "e2e/basic-greeting":
    raise AssertionError(f"implementation left guarded branch: {branch!r}")

subprocess.run(["git", "diff", "--check"], cwd=repository, check=True)
subprocess.run(["python3", "-m", "unittest", "-v"], cwd=repository, check=True)

test_source = (repository / "test_greeting.py").read_text()
if 'self.assertEqual(greet("Ada"), "Hello, Ada!")' not in test_source:
    raise AssertionError("focused greeting test does not assert the requested behavior")
