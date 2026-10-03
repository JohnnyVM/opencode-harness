"""Require exact package handoffs and a completed DONE implementation report."""

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
specification = repository / "docs/spec/brand-selection.md"
architecture = repository / "docs/spec/brand-selection-architecture.md"
if not specification.is_file():
    raise AssertionError("spec-orchestrator did not create the specification file")
if not architecture.is_file():
    raise AssertionError("architect did not create the default architecture file")
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
if branch != "e2e/brand-selection":
    raise AssertionError(f"implementation left guarded branch: {branch!r}")

subprocess.run(["git", "diff", "--check"], cwd=repository, check=True)
