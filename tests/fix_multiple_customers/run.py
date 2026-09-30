"""Generate a specification, architect it, then implement the architecture."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


workspace = Path(os.environ["TEST_WORKSPACE"])
specification = ".scratch/fix-multiple-customers-specification.md"
capture_agents(
    repository=workspace / "tmp",
    artifacts=Path(os.environ["TEST_ARTIFACTS"]),
    harness=Path(__file__).resolve().parents[2],
    invocations=[
        {
            "stage": "specification",
            "agent": "spec-orchestrator",
            "prompt": (
                "Work autonomously. Convert the supplied issue requirements into "
                "a complete agent-approved Specification Package. Resolve non-product "
                "ambiguities with documented assumptions; ask no questions. Write "
                f"only {specification}.\n\n"
                + Path(__file__).with_name("issue.md").read_text()
            ),
        },
        {
            "stage": "architecture",
            "agent": "architect",
            "command": "architect",
            "prompt": f"{specification} --output .scratch/fix-multiple-customers-architecture.md",
        },
        {
            "stage": "implementation",
            "agent": "implementation-orchestrator",
            "command": "implement",
            "prompt": ".scratch/fix-multiple-customers-architecture.md",
        },
    ],
)
