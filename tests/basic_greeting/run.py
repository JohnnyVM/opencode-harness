"""Generate a specification, architect it, then implement the architecture."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


HARNESS_CONFIG = Path(__file__).resolve().parents[2] / "opencode"

PROMPT = f"""Work autonomously and generate a Specification Package for this feature.
Do not ask questions: use recommended defaults for non-product ambiguities,
record them as assumptions, and write no file except the requested package.
Use the Specification Package contract at {HARNESS_CONFIG / 'contracts/specification-package.md'}
and validate with {HARNESS_CONFIG / 'scripts/validate_specification_package.py'}
instead of the globally installed copies.

Change the greeting behavior so greet(name) returns the exact text
"Hello, <name>!". Update the focused automated test for this behavior. Require
both the focused unit test and `git diff --check` to pass before completion.

Generate the complete agent-approved specification at
.scratch/basic-greeting-specification.md.
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
            "prompt": ".scratch/basic-greeting-specification.md --output .scratch/basic-greeting-architecture.md",
        },
        {
            "stage": "implementation",
            "agent": "implementation-orchestrator",
            "command": "implement",
            "prompt": ".scratch/basic-greeting-architecture.md",
        },
    ],
)
