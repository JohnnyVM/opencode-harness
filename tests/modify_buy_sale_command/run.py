"""Ask spec-orchestrator for a package, then ask the orchestrator to implement it."""

import os
from pathlib import Path

from scripts.lifecycle_opencode import capture_agents


HARNESS_CONFIG = Path(__file__).resolve().parents[2] / "opencode"

PROMPT = f"""Work autonomously and generate a Specification Package for this feature.
Do not ask questions: use your recommended defaults for non-product ambiguities,
record them as assumptions, and write no file except the requested package.
Use the contract at {HARNESS_CONFIG / 'contracts/specification-package.md'}
and validator at {HARNESS_CONFIG / 'scripts/validate_specification_package.py'}
instead of globally installed copies.

Modify the @buy and @sale commands to accept default_code as a product
identifier. An all-digit product argument is a barcode; other product arguments
are default_code values. A partner name can be one word, and names containing
spaces must be quoted, for example "name surname".

example:
@buy "azeta s.l" FC045 9999999999

Generate the complete agent-approved specification at
.scratch/modify-buy-sale-command-specification.md.
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
            "prompt": ".scratch/modify-buy-sale-command-specification.md --output .scratch/modify-buy-sale-command-architecture.md",
        },
        {
            "stage": "implementation",
            "agent": "implementation-orchestrator",
            "command": "implement",
            "prompt": ".scratch/modify-buy-sale-command-architecture.md",
        },
    ],
)
