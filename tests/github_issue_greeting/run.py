"""Architect and implement the local greeting specification."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


workspace = Path(os.environ["TEST_WORKSPACE"])
capture_agents(
    repository=workspace / "tmp",
    artifacts=Path(os.environ["TEST_ARTIFACTS"]),
    harness=Path(__file__).resolve().parents[2],
    invocations=[
        {
            "stage": "architecture",
            "agent": "architect",
            "command": "architect",
            "prompt": ".scratch/greeting-specification.md --output .scratch/greeting-architecture.md",
        },
        {
            "stage": "implementation",
            "agent": "implementation-orchestrator",
            "command": "implement",
            "prompt": ".scratch/greeting-architecture.md",
        },
    ],
)
