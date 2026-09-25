"""Generate a package from a user request, then implement it via /implement."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


PROMPT = """Work autonomously and generate an implementation package for this feature.
Do not ask questions: use recommended defaults for non-product ambiguities,
record them as assumptions, and write no file except the requested package.

Change the greeting behavior so greet(name) returns the exact text
"Hello, <name>!". Update the focused automated test for this behavior.

Generate the complete agent-approved spec file at .scratch/basic-greeting.md.
"""

workspace = Path(os.environ["TEST_WORKSPACE"])
capture_agents(
    repository=workspace / "tmp",
    artifacts=Path(os.environ["TEST_ARTIFACTS"]),
    harness=Path(__file__).resolve().parents[2],
    invocations=[
        {"stage": "spec-orchestrator", "agent": "spec-orchestrator", "prompt": PROMPT},
        {
            "stage": "implementation",
            "agent": "spec-orchestrator",
            "command": "implement",
            "prompt": ".scratch/basic-greeting.md",
        },
    ],
)
