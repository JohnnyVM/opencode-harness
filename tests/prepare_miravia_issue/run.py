"""Run the actual /implement GitHub-issue command against the pinned clone."""

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
            "stage": "implementation",
            "agent": "spec-orchestrator",
            "command": "implement",
            "prompt": "Guadalsistema/connector-proyect#10",
        },
    ],
)
