"""Run brand selection through specification, architecture, and implementation."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


HARNESS_CONFIG = Path(__file__).resolve().parents[2] / "opencode"

PROMPT = f"""I need modify how the brands are select:
Here the search button doesnt ahve any indication of the available brands.
Seller brands should list the list of brands in canonical products for the user

Require all Go test commands used during implementation, including baseline
and focused checks, to include -v so captured output shows individual test
names and progress.

Work autonomously and do not stop to ask questions. Resolve ambiguities using
your recommended defaults and record assumptions in the specification.
Generate the complete agent-approved Specification Package in
./docs/spec/brand-selection.md. Write no file except the requested package.
Use the contract at {HARNESS_CONFIG / 'contracts/specification-package.md'}
and validator at {HARNESS_CONFIG / 'scripts/validate_specification_package.py'}
instead of globally installed copies.
"""

workspace = Path(os.environ["TEST_WORKSPACE"])
capture_agents(
    repository=workspace / "tmp",
    artifacts=Path(os.environ["TEST_ARTIFACTS"]),
    harness=HARNESS_CONFIG.parent,
    invocations=[
        {"stage": "specification", "agent": "spec-orchestrator", "prompt": PROMPT},
        {
            "stage": "architecture",
            "agent": "architect",
            "command": "architect",
            "prompt": "./docs/spec/brand-selection.md",
        },
        {
            "stage": "implementation",
            "agent": "implementation-orchestrator",
            "command": "implement",
            "prompt": "./docs/spec/brand-selection-architecture.md",
        },
    ],
)
