"""Ask spec-design for a package, then ask the orchestrator to implement it."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


PROMPT = """I want modify the @buy and @sale command to add the following feature:
Sccept default_code as product identifier arguments, currently only accept barcodes,a barcode is identified as words with all numbers for that
names can be only one word, if the name have spacesmultbe expresed with "" like "name surmane"

example:
@buy "azeta s.l" FC045 9999999999

Generate the spec file in the folder .scratch/modify-buy-sale-command.md
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
            "prompt": "/implement .scratch/modify-buy-sale-command.md",
        },
    ],
)
