"""Run OpenCode's plan agent and redirect its response to a file."""

import os
from pathlib import Path
import shutil
import subprocess


workspace = Path(os.environ["TEST_WORKSPACE"])
temp = workspace / "tmp"
output = temp / "output.txt"
opencode = shutil.which("opencode")
if not opencode:
    raise RuntimeError("opencode CLI is not installed")

prompt = "Say the exact word 'hi!' Don't answer anything more."
with output.open("w") as stream:
    subprocess.run(
        [opencode, "run", "--pure", "--agent", "plan", prompt],
        cwd=temp,
        stdout=stream,
        check=True,
    )
