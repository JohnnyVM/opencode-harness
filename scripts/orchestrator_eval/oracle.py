"""The small, deliberately boring protocol adapter for an external Oracle.

The Oracle is untrusted: it is given a frozen verification directory and a
sanitised environment, and its output is accepted only when it is one JSON
object.  Everything else is a harness error, rather than an evaluation fail.
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence


class OracleProtocolError(RuntimeError):
    """The Oracle did not implement the versioned wire protocol."""


@dataclass(frozen=True)
class OracleResult:
    outcome: str
    details: Any
    duration: float = 0.0
    model: str | None = None


def oracle_environment(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return an environment with credentials and publication variables removed."""
    result = dict(os.environ if env is None else env)
    needles = ("TOKEN", "PASSWORD", "SECRET", "CREDENTIAL", "API_KEY", "PRIVATE_KEY")
    for key in list(result):
        upper = key.upper()
        if any(needle in upper for needle in needles):
            result.pop(key, None)
    result["OPENCODE_EVALUATION_FROZEN"] = "1"
    return result


def _decode(stdout: str) -> Mapping[str, Any]:
    try:
        value = json.loads(stdout)
    except (TypeError, json.JSONDecodeError) as error:
        raise OracleProtocolError("Oracle output is not JSON") from error
    if not isinstance(value, dict):
        raise OracleProtocolError("Oracle result must be a JSON object")
    if set(value) - {"outcome", "status", "details", "model", "duration", "checks"}:
        raise OracleProtocolError("Oracle result contains unknown fields")
    outcome = value.get("outcome", value.get("status"))
    if outcome not in {"PASS", "FAIL", "SKIP"}:
        raise OracleProtocolError("Oracle result has an invalid outcome")
    return value


def run_oracle(command: Sequence[str], request: Mapping[str, Any], *, verification_root: Path,
               timeout: float | None = None,
               runner: Callable[..., subprocess.CompletedProcess] | None = None) -> OracleResult:
    """Run Oracle in the frozen copy and reduce its one-result response."""
    if not command:
        raise OracleProtocolError("Oracle command is empty")
    runner = runner or subprocess.run
    started = time.monotonic()
    try:
        completed = runner(list(command), input=json.dumps(request, sort_keys=True), text=True,
                           capture_output=True, cwd=Path(verification_root),
                           env=oracle_environment(), timeout=timeout, check=False)
        if completed.returncode != 0:
            raise OracleProtocolError("Oracle exited unsuccessfully")
        value = _decode(completed.stdout)
    except OracleProtocolError:
        raise
    except Exception as error:
        raise OracleProtocolError(f"Oracle execution failed: {error}") from error
    details = value.get("details", value.get("checks", {}))
    if not isinstance(details, (dict, list)):
        raise OracleProtocolError("Oracle details must be an object or array")
    duration = value.get("duration", 0.0)
    if not isinstance(duration, (int, float)) or isinstance(duration, bool):
        raise OracleProtocolError("Oracle duration must be numeric")
    model = value.get("model")
    if model is not None and not isinstance(model, str):
        raise OracleProtocolError("Oracle model must be a string")
    # The result's model is authoritative, while elapsed time is measured by
    # the harness (a claimed duration is retained only as protocol metadata).
    elapsed = time.monotonic() - started
    return OracleResult(value.get("outcome", value.get("status")), details, elapsed, model)


def reduce_results(results: Sequence[OracleResult | Mapping[str, Any]]) -> str:
    """PASS is conjunctive; a protocol error is represented by the caller."""
    if not results:
        return "SKIP"
    outcomes = [result.outcome if isinstance(result, OracleResult)
                else result.get("outcome", result.get("status")) for result in results]
    if any(outcome == "FAIL" for outcome in outcomes):
        return "FAIL"
    if any(outcome == "SKIP" for outcome in outcomes):
        return "SKIP"
    return "PASS"


reduce_oracle_results = reduce_results
