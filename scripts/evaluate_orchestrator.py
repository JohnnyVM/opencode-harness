"""CLI adapter for orchestrator evaluation cases."""

import sys

try:  # Support both ``python scripts/evaluate_orchestrator.py`` and ``-m``.
    from .orchestrator_eval.cli import main
except ImportError:  # pragma: no cover - exercised by direct script launch.
    from orchestrator_eval.cli import main


if __name__ == "__main__":
    sys.exit(main())
