"""Create the input consumed by the test action."""

import os
from pathlib import Path


workspace = Path(os.environ["TEST_WORKSPACE"])
(workspace / "input.txt").write_text("opencode harness\n")
