"""Orchestration and outcome precedence for evaluation runs."""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .oracle import OracleProtocolError, OracleResult, reduce_results, run_oracle
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
