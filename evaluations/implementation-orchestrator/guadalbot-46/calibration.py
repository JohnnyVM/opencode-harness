"""Deterministic calibration for the bundled oracle; no network or candidate code."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent


def main() -> int:
    request = json.loads((ROOT / "request.json").read_text(encoding="utf-8"))
    request["observations"] = {
        "buy": {"result": "buy"},
        "sale": {"result": "sale"},
        "ambiguous": {"result": "ambiguous"},
        "diagnostic": {"result": "ambiguous", "stderr": "invalid request"},
    }
    result = subprocess.run([sys.executable, str(ROOT / "oracle.py")],
                            input=json.dumps(request), text=True,
                            capture_output=True, check=False)
    if result.returncode or json.loads(result.stdout).get("outcome") != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
