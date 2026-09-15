"""Ask spec-design to analyze issue 46, then ask the orchestrator to implement it."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


workspace = Path(os.environ["TEST_WORKSPACE"])
issue = Path(__file__).with_name("issue.md")
capture_agents(
    repository=workspace / "tmp",
    artifacts=Path(os.environ["TEST_ARTIFACTS"]),
    harness=Path(__file__).resolve().parents[2],
    invocations=[
        {
            "stage": "spec-design",
            "agent": "spec-design",
            "prompt": "Analyze the attached issue and follow its instructions.",
            "files": (issue,),
        },
        {
            "stage": "implementation",
            "agent": "implementation-orchestrator",
            "prompt": "implement .scratch/fix-multiple-customers.md",
        },
    ],
)
