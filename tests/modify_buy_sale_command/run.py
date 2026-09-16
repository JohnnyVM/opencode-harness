"""Ask spec-design for a package, then ask the orchestrator to implement it."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


PROMPT = """Work autonomously and generate an implementation package for this feature.
Do not ask questions: use your recommended defaults for non-product ambiguities,
record them as assumptions, and write no file except the requested package.

Modify the @buy and @sale commands to accept default_code as a product
identifier. An all-digit product argument is a barcode; other product arguments
are default_code values. A partner name can be one word, and names containing
spaces must be quoted, for example "name surname".

example:
@buy "azeta s.l" FC045 9999999999

Generate the complete agent-approved spec file at
.scratch/modify-buy-sale-command.md
"""

workspace = Path(os.environ["TEST_WORKSPACE"])
capture_agents(
    repository=workspace / "tmp",
    artifacts=Path(os.environ["TEST_ARTIFACTS"]),
    harness=Path(__file__).resolve().parents[2],
    invocations=[
        {"stage": "spec-design", "agent": "spec-design", "prompt": PROMPT},
        {
            "stage": "implementation",
            "agent": "implementation-orchestrator",
            "prompt": ".scratch/modify-buy-sale-command.md",
        },
    ],
)
