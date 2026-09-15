"""Create the temporary directory used for the OpenCode invocation."""

import os
from pathlib import Path


workspace = Path(os.environ["TEST_WORKSPACE"])
(workspace / "tmp").mkdir()
