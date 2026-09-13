"""Orchestration and outcome precedence for evaluation runs."""

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from .case import EvaluationCase, Status, load_case
from .environment import DoctorReport, check_prerequisites
from .oracle import OracleProtocolError, OracleResult, reduce_results, run_oracle
from .process import run_command
from .report import write_report


# Keep the conventional command-line contract: assertion failure is distinct
# from an evaluator failure, while a skipped run is not a failed evaluation.
OUTCOME_EXIT = {"PASS": 0, "FAIL": 1, "HARNESS_ERROR": 2, "SKIP": 0}


@dataclass(frozen=True)
class HarnessResult:
    outcome: str
    exit_code: int
    result: Mapping[str, Any]


def run_oracles(commands: Sequence[Sequence[str]], request: Mapping[str, Any], *, verification_root,
                output_root=None, timeout=None, raw=None) -> HarnessResult:
    results: list[OracleResult] = []
    try:
        for command in commands:
            results.append(run_oracle(command, request, verification_root=verification_root, timeout=timeout))
    except OracleProtocolError as error:
        payload = {"outcome": "HARNESS_ERROR", "error": str(error), "results": [r.__dict__ for r in results]}
        if output_root is not None:
            write_report(output_root, payload, raw=raw)
        return HarnessResult("HARNESS_ERROR", OUTCOME_EXIT["HARNESS_ERROR"], payload)
    outcome = reduce_results(results)
    payload = {
        "outcome": outcome,
        "model": next((r.model for r in results if r.model), None),
        "timings": {"oracle": sum(r.duration for r in results)},
        "results": [r.__dict__ for r in results],
    }
    if output_root is not None:
        write_report(output_root, payload, raw=raw)
    return HarnessResult(outcome, OUTCOME_EXIT[outcome], payload)


def outcome_exit(outcome: str) -> int:
    return OUTCOME_EXIT.get(outcome, OUTCOME_EXIT["HARNESS_ERROR"])


def doctor_case(case_id: str, source_repo: Path) -> tuple[EvaluationCase, DoctorReport]:
    """Load the case and perform the prerequisite phase without side effects."""
    case = load_case(case_id, source_repo)
    # Docker is not required by the local command/Oracle protocol.  Callers
    # that use a container-backed runner can supply that check separately.
    return case, check_prerequisites(required_tools=())


def run_evaluation(case: EvaluationCase, source_repo: Path, *, output_root: Path | None = None,
                   discard_raw: bool = False) -> HarnessResult:
    """Run the case commands, then publish one authoritative report."""
    records = []
    raw_parts = []
    try:
        root = Path(source_repo).resolve()
        for command in case.commands:
            result = run_command(command, cwd=root / command.cwd)
            expected = result.exit_code == int(command.expected_exit_code)
            status_ok = (command.expected_status is Status.PASSED and expected) or (
                command.expected_status is not Status.PASSED and not expected)
            records.append({"name": command.name, "status": "PASS" if status_ok else "FAIL",
                            "exit_code": result.exit_code, "duration": result.duration})
            raw_parts.append(result.stdout.decode(errors="replace"))
        outcome = "PASS" if all(item["status"] == "PASS" for item in records) else "FAIL"
        payload = {"outcome": outcome, "case_id": case.case_id,
                   "timings": {"commands": sum(item["duration"] for item in records)},
                   "results": records}
    except Exception as error:
        outcome = "HARNESS_ERROR"
        payload = {"outcome": outcome, "case_id": case.case_id, "error": str(error),
                   "results": records}
    if output_root is not None:
        write_report(output_root, payload, raw=None if discard_raw else "".join(raw_parts))
    return HarnessResult(outcome, outcome_exit(outcome), payload)
