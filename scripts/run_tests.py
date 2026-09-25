#!/usr/bin/env python3
"""Run directory-based lifecycle tests."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
PHASES = ("prepare.py", "run.py", "validate.py")
MODEL_FLAGS = {
    "spec_model": "TEST_SPEC_MODEL",
    "implementation_model": "TEST_IMPLEMENTATION_MODEL",
    "coder_light_model": "TEST_CODER_LIGHT_MODEL",
    "coder_heavy_model": "TEST_CODER_HEAVY_MODEL",
}
ENABLED_MCPS_ENV = "TEST_ENABLED_MCPS"
DISABLED_MCPS_ENV = "TEST_DISABLED_MCPS"
MCP_NAMES = ("playwright", "ripwire")


def model_id(value):
    if (
        not value
        or "/" not in value
        or any(not part for part in value.split("/"))
        or any(char.isspace() for char in value)
    ):
        raise argparse.ArgumentTypeError("model must be in provider/model format")
    return value


def mcp_name(value):
    if value not in MCP_NAMES:
        raise argparse.ArgumentTypeError(
            f"unknown MCP {value!r}; expected one of: {', '.join(MCP_NAMES)}"
        )
    return value


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


def cleanup_artifacts(tests):
    """Remove persisted artifacts for the selected lifecycle tests."""
    for test in tests:
        artifacts = ROOT / "artifacts" / test.name
        if artifacts.exists():
            print(f"[{test.name}] removing previous artifacts", flush=True)
            shutil.rmtree(artifacts)


def run_test(test, workspace, artifacts, settings=None):
    environment = os.environ.copy()
    settings = settings or {}
    for key in MODEL_FLAGS.values():
        environment.pop(key, None)
    for name, value in settings.get("models", {}).items():
        if value is not None:
            environment[MODEL_FLAGS[name]] = value
    environment[ENABLED_MCPS_ENV] = ",".join(settings.get("enabled_mcps", ()))
    environment[DISABLED_MCPS_ENV] = ",".join(settings.get("disabled_mcps", ()))
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
    for name in MODEL_FLAGS:
        parser.add_argument(
            f"--{name.replace('_', '-')}",
            type=model_id,
            help="override the model for this agent (provider/model)",
        )
    parser.add_argument("--mcp", action="append", type=mcp_name, default=[], metavar="NAME",
                        help="enable an MCP server; repeat for multiple servers")
    parser.add_argument("--no-mcp", action="append", type=mcp_name, default=[], metavar="NAME",
                        help="disable an MCP server; repeat for multiple servers")
    parser.add_argument("--clean", action="store_true",
                        help="remove previous artifacts for selected tests before running")
    arguments = parser.parse_args()
    models = {name: getattr(arguments, name) for name in MODEL_FLAGS}
    conflicting_mcps = sorted(set(arguments.mcp) & set(arguments.no_mcp))
    if conflicting_mcps:
        parser.error(f"MCPs cannot be both enabled and disabled: {', '.join(conflicting_mcps)}")

    tests, errors = discover_tests(arguments.tests)
    if errors:
        for error in errors:
            print(f"Invalid test: {error}", file=sys.stderr)
        return 1
    if not tests:
        print(f"No lifecycle tests found in {TESTS}", file=sys.stderr)
        return 1
    if arguments.clean:
        cleanup_artifacts(tests)

    failures = []
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    with tempfile.TemporaryDirectory(prefix="opencode-harness-tests-") as temp:
        workspace_root = Path(temp)
        for test in tests:
            workspace = workspace_root / test.name
            workspace.mkdir()
            artifacts = ROOT / "artifacts" / test.name / run_id
            if not run_test(test, workspace, artifacts, {
                "models": models,
                "enabled_mcps": arguments.mcp,
                "disabled_mcps": arguments.no_mcp,
            }):
                failures.append(test.name)

    print(f"\n{len(tests) - len(failures)}/{len(tests)} lifecycle tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
