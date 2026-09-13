"""Prerequisite checks for the orchestrator evaluation.

The checker is deliberately boring: every check is attempted on every run and
dependency failures are represented as skipped checks rather than hiding later
failures behind the first missing tool.  ``runner`` and ``which`` are injectable
so this module can be tested without Docker, network access, or a host install.
"""

from dataclasses import dataclass
import platform
import shutil
import subprocess
from typing import Callable, Iterable, Mapping


@dataclass(frozen=True)
class Check:
    name: str
    status: str  # passed, failed, skipped
    detail: str = ""


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[Check, ...]

    @property
    def ok(self) -> bool:
        return all(check.status != "failed" for check in self.checks)

    @property
    def failed(self) -> tuple[Check, ...]:
        return tuple(c for c in self.checks if c.status == "failed")


def check_prerequisites(
    *,
    required_tools: Iterable[str] = ("git", "docker"),
    versions: Mapping[str, str] | None = None,
    image: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess] | None = None,
    which: Callable[[str], str | None] | None = None,
) -> DoctorReport:
    """Run a fresh, exhaustive prerequisite inspection.

    Version and image queries are informational checks and never pull or build
    anything.  An unavailable tool causes its dependent query to be skipped,
    while all independent checks continue.
    """
    runner = runner or subprocess.run
    which = which or shutil.which
    checks: list[Check] = []
    system = platform.system()
    checks.append(Check("platform.linux", "passed" if system == "Linux" else "failed", system))
    arch = platform.machine()
    checks.append(Check("platform.architecture", "passed" if arch else "failed", arch or "unknown"))
    available: dict[str, bool] = {}
    for tool in required_tools:
        found = which(tool)
        available[tool] = bool(found)
        checks.append(Check(f"tool.{tool}", "passed" if found else "failed", found or "not found"))
    for tool, expected in (versions or {}).items():
        if not available.get(tool, bool(which(tool))):
            checks.append(Check(f"version.{tool}", "skipped", "tool unavailable"))
            continue
        try:
            result = runner([tool, "--version"], capture_output=True, text=True, check=False)
            text = (result.stdout or result.stderr or "").strip()
            checks.append(Check(f"version.{tool}", "passed" if result.returncode == 0 and expected in text else "failed", text))
        except OSError as error:
            checks.append(Check(f"version.{tool}", "failed", str(error)))
    if image:
        if not available.get("docker", bool(which("docker"))):
            checks.append(Check("image", "skipped", "docker unavailable"))
        else:
            try:
                result = runner(["docker", "image", "inspect", image], capture_output=True, text=True, check=False)
                checks.append(Check("image", "passed" if result.returncode == 0 else "failed", image))
            except OSError as error:
                checks.append(Check("image", "failed", str(error)))
    return DoctorReport(tuple(checks))


doctor = check_prerequisites
