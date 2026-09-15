"""Validate the result produced by the test action."""

import os
from pathlib import Path


workspace = Path(os.environ["TEST_WORKSPACE"])
actual = (workspace / "output.txt").read_text()
expected = "OPENCODE HARNESS\n"
if actual != expected:
    raise AssertionError(f"expected {expected!r}, got {actual!r}")
