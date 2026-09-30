"""Generate a specification, architect it, then implement the architecture."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


PROMPT = """Work autonomously and generate a Specification Package for this feature.
Do not ask questions: use recommended defaults for non-product ambiguities,
record them as assumptions, and write no file except the requested package.

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
    harness=Path(__file__).resolve().parents[2],
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
