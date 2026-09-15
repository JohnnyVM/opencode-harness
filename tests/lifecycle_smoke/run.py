"""Exercise the behavior under test."""

import os
from pathlib import Path


workspace = Path(os.environ["TEST_WORKSPACE"])
source = (workspace / "input.txt").read_text()
(workspace / "output.txt").write_text(source.upper())
