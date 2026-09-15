"""Require the OpenCode response to contain exactly the requested word."""

import os
from pathlib import Path


workspace = Path(os.environ["TEST_WORKSPACE"])
actual = (workspace / "tmp" / "output.txt").read_text()
if actual not in ("hi!", "hi!\n"):
    raise AssertionError(f"expected exactly 'hi!', got {actual!r}")
