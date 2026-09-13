"""Independent, offline Guadalbot #46 oracle.

The oracle consumes a JSON request and emits exactly one protocol object.  It
does not import candidate code: the harness supplies candidate observations in
``observations``.  This keeps equivalent implementations interchangeable.
"""

import json
import sys


def main() -> int:
    request = json.load(sys.stdin)
    observations = request.get("observations", {})
    checks = []
    for check in request.get("checks", []):
        name = check["name"]
        actual = observations.get(name, {})
        passed = actual.get("result") == check.get("expected")
        if check.get("expected_stderr"):
            passed = passed and bool(actual.get("stderr"))
        checks.append({"name": name, "passed": passed})
    print(json.dumps({"outcome": "PASS" if checks and all(c["passed"] for c in checks) else "FAIL",
                      "details": checks, "model": "independent-offline"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
