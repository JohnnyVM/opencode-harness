"""Strict schema for orchestrator evaluation cases.

The loader deliberately does not import or execute anything from a case.  Case
manifests are data, and paths in them are confined to the source repository.
"""

from dataclasses import dataclass
from enum import Enum, IntEnum
import json
from pathlib import Path, PureWindowsPath
from typing import Any


class CaseError(ValueError):
    """A case is missing, malformed, or unsafe to load."""


class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class ExitCode(IntEnum):
    SUCCESS = 0
    FAILURE = 1
    USAGE = 2

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 255:
            member = int.__new__(cls, value)
            member._name_ = f"CODE_{value}"
            member._value_ = value
            cls._value2member_map_[value] = member
            return member
        return None


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CaseError(f"{label} must be a non-empty string")
    return value


def _safe_relative(value: Any, label: str) -> str:
    value = _string(value, label)
    if "\x00" in value:
        raise CaseError(f"{label} must be a repository-relative path")
    path = Path(value)
    windows_path = PureWindowsPath(value)
    if path.is_absolute() or windows_path.is_absolute() or ".." in path.parts or ".." in windows_path.parts:
        raise CaseError(f"{label} must be a repository-relative path")
    return value


@dataclass(frozen=True)
class CommandRecord:
    name: str
    argv: tuple[str, ...]
    cwd: str = "."
    expected_status: Status = Status.PASSED
    expected_exit_code: ExitCode = ExitCode.SUCCESS

    @classmethod
    def from_mapping(cls, raw: Any) -> "CommandRecord":
        if not isinstance(raw, dict):
            raise CaseError("command records must be objects")
        allowed = {"name", "argv", "cwd", "expected_status", "expected_exit_code"}
        unknown = set(raw) - allowed
        if unknown:
            raise CaseError(f"unknown command key(s): {', '.join(sorted(unknown))}")
        if "name" not in raw or "argv" not in raw:
            raise CaseError("command records require name and argv")
        argv = raw["argv"]
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise CaseError("command argv must be a non-empty list of strings")
        cwd = _safe_relative(raw.get("cwd", "."), "command cwd")
        try:
            status = Status(raw.get("expected_status", Status.PASSED.value))
        except ValueError as error:
            raise CaseError("invalid command expected_status") from error
        code = raw.get("expected_exit_code", int(ExitCode.SUCCESS))
        if not isinstance(code, int) or isinstance(code, bool) or code < 0 or code > 255:
            raise CaseError("expected_exit_code must be an integer from 0 to 255")
        try:
            exit_code = ExitCode(code)
        except ValueError as error:
            raise CaseError("expected_exit_code must be an integer from 0 to 255") from error
        return cls(_string(raw["name"], "command name"), tuple(argv), cwd, status, exit_code)


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    schema_version: int
    commands: tuple[CommandRecord, ...]
    description: str = ""
    assets: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, raw: Any, expected_id: str) -> "EvaluationCase":
        if not isinstance(raw, dict):
            raise CaseError("case manifest must be an object")
        allowed = {"schema_version", "case_id", "description", "commands", "assets"}
        unknown = set(raw) - allowed
        if unknown:
            raise CaseError(f"unknown case key(s): {', '.join(sorted(unknown))}")
        if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
            raise CaseError("case schema_version must be 1")
        if raw.get("case_id") != expected_id:
            raise CaseError(f"manifest case_id must be {expected_id}")
        commands = raw.get("commands")
        if not isinstance(commands, list) or not commands:
            raise CaseError("case commands must be a non-empty list")
        description = raw.get("description", "")
        if not isinstance(description, str):
            raise CaseError("case description must be a string")
        assets = raw.get("assets", [])
        if not isinstance(assets, list):
            raise CaseError("case assets must be a list")
        safe_assets = tuple(_safe_relative(asset, "case asset") for asset in assets)
        return cls(
            expected_id,
            1,
            tuple(CommandRecord.from_mapping(x) for x in commands),
            description,
            safe_assets,
        )


def _manifest_path(source_repo: Path, case_id: str) -> Path:
    # Keep the accepted locations explicit; this also prevents a case name
    # from becoming an arbitrary filesystem path.
    for relative in (
        Path("evaluations") / "implementation-orchestrator" / case_id / "manifest.json",
        Path("evaluation-cases") / case_id / "manifest.json",
        Path("cases") / case_id / "manifest.json",
        Path(".opencode-harness") / "cases" / case_id / "manifest.json",
    ):
        candidate = source_repo / relative
        if candidate.is_file():
            return candidate
    raise CaseError(f"case manifest not found: {case_id}")


def _reject_symlink_path(path: Path, root: Path) -> None:
    current = root
    for part in path.relative_to(root).parts:
        current /= part
        if current.is_symlink():
            raise CaseError(f"case path uses a symlink: {current}")


def load_case(case_id: str, source_repo: str | Path) -> EvaluationCase:
    if case_id != "guadalbot-46":
        raise CaseError(f"unknown case: {case_id} (only guadalbot-46 is supported)")
    root = Path(source_repo).resolve()
    if not root.is_dir():
        raise CaseError(f"source repository is not a directory: {source_repo}")
    manifest = _manifest_path(root, case_id)
    _reject_symlink_path(manifest, root)
    try:
        raw = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CaseError(f"cannot read case manifest {manifest}: {error}") from error
    case = EvaluationCase.from_mapping(raw, case_id)
    for command in case.commands:
        # Check the complete lexical path, including components that do not
        # exist yet (a broken symlink must not become an escape later).
        _reject_symlink_path(root / command.cwd, root)
    for asset in case.assets:
        _reject_symlink_path(root / asset, root)
    return case
