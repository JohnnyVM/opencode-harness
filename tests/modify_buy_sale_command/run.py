"""Ask spec-design for a package, then ask the orchestrator to implement it."""

import os
from pathlib import Path
import shutil
import subprocess


PROMPT = """I want modify the @buy and @sale command to add the following feature:
Sccept default_code as product identifier arguments, currently only accept barcodes,a barcode is identified as words with all numbers for that
names can be only one word, if the name have spacesmultbe expresed with "" like "name surmane"

example:
@buy "azeta s.l" FC045 9999999999

Generate the spec file in the folder .scratch/modify-buy-sale-command.md
"""

workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
harness = Path(__file__).resolve().parents[2]
opencode = shutil.which("opencode")
if not opencode:
    raise RuntimeError("opencode CLI is not installed")

environment = os.environ.copy()
environment.update(
    {
        "OPENCODE_CONFIG": str(harness / "opencode" / "opencode.jsonc"),
        "OPENCODE_CONFIG_DIR": str(harness / "opencode"),
        "OPENCODE_CONFIG_CONTENT": '{"mcp":{"playwright":{"enabled":false}}}',
        "OPENCODE_DISABLE_MODELS_FETCH": "1",
        "OPENCODE_DISABLE_LSP_DOWNLOAD": "1",
    }
)

with (workspace / "spec-design.log").open("w") as output:
    subprocess.run(
        [opencode, "run", "--pure", "--agent", "spec-design", PROMPT],
        cwd=repository,
        env=environment,
        stdout=output,
        check=True,
    )

with (workspace / "implementation.log").open("w") as output:
    subprocess.run(
        [
            opencode,
            "run",
            "--pure",
            "--agent",
            "implementation-orchestrator",
            "/implement .scratch/modify-buy-sale-command.md",
        ],
        cwd=repository,
        env=environment,
        stdout=output,
        check=True,
    )
