#!/usr/bin/env python3
"""Run directory-based lifecycle tests."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
PHASES = ("prepare.py", "run.py", "validate.py")


def discover_tests(selected):
    tests = []
    errors = []
    for path in sorted(TESTS.iterdir()):
        if not path.is_dir() or path.name.startswith((".", "__")):
            continue
        present = [phase for phase in PHASES if (path / phase).is_file()]
        if not present:
            continue
        missing = [phase for phase in PHASES if phase not in present]
        if missing:
            errors.append(f"{path.name}: missing {', '.join(missing)}")
        else:
            tests.append(path)
    if selected:
        discovered = {test.name: test for test in tests}
        unknown = sorted(set(selected) - discovered.keys())
        errors.extend(f"{name}: not found" for name in unknown)
        tests = [discovered[name] for name in selected if name in discovered]
    return tests, errors


def run_test(test, workspace, artifacts):
    environment = os.environ.copy()
    environment["TEST_WORKSPACE"] = str(workspace)
    environment["TEST_ARTIFACTS"] = str(artifacts)
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(ROOT), environment.get("PYTHONPATH")) if value
    )

    for phase in PHASES:
        print(f"[{test.name}] {phase}", flush=True)
        result = subprocess.run(
            [sys.executable, phase],
            cwd=test,
            env=environment,
            check=False,
        )
        if result.returncode:
            print(
                f"[{test.name}] FAILED in {phase} (exit {result.returncode})",
                file=sys.stderr,
            )
            return False

    print(f"[{test.name}] PASSED")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tests", nargs="*", help="test directory names (default: all)")
    arguments = parser.parse_args()

    tests, errors = discover_tests(arguments.tests)
    if errors:
        for error in errors:
            print(f"Invalid test: {error}", file=sys.stderr)
        return 1
    if not tests:
        print(f"No lifecycle tests found in {TESTS}", file=sys.stderr)
        return 1

    failures = []
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    with tempfile.TemporaryDirectory(prefix="opencode-harness-tests-") as temp:
        workspace_root = Path(temp)
        for test in tests:
            workspace = workspace_root / test.name
            workspace.mkdir()
            artifacts = ROOT / "artifacts" / test.name / run_id
            if not run_test(test, workspace, artifacts):
                failures.append(test.name)

    print(f"\n{len(tests) - len(failures)}/{len(tests)} lifecycle tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
