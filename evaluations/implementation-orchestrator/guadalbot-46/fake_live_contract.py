"""Fake-only contract probe used by tests and local calibration.

Real OpenCode execution is deliberately opt-in and is never started here.
"""

import json
import os
import sys


def main() -> int:
    if os.environ.get("GUADALBOT46_LIVE") == "1":
        print("live execution requires an explicitly configured external runner", file=sys.stderr)
        return 2
    print(json.dumps({"outcome": "SKIP", "details": {"live": "opt-in only"}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
