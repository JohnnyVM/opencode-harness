"""Run OpenCode using its machine-readable stdin interface.

This module intentionally keeps the invocation small and explicit.  In
particular, model selection belongs to the OpenCode configuration, not to an
evaluation command line.
"""

from dataclasses import dataclass
import json
import re
import subprocess
from typing import Any, Callable, Iterable, Mapping, Sequence


OPENCODE_ARGV = ("opencode", "run", "--format", "json")


@dataclass(frozen=True)
class OpenCodeResult:
    exit_code: int
    events: tuple[Mapping[str, Any], ...]
    stdout: str
    stderr: str
    duration: float = 0.0


def opencode_argv() -> tuple[str, ...]:
    """The sole supported OpenCode invocation (stdin supplies the prompt)."""
    return OPENCODE_ARGV


def parse_jsonl(stdout: str) -> tuple[Mapping[str, Any], ...]:
    """Parse strict JSONL output, rejecting blank or non-object lines."""
    events = []
    for number, line in enumerate(stdout.splitlines(), 1):
        if not line.strip():
            raise ValueError(f"OpenCode stdout line {number} is not JSONL")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid OpenCode JSONL at line {number}") from error
        if not isinstance(value, dict):
            raise ValueError(f"OpenCode JSONL line {number} is not an object")
        events.append(value)
    return tuple(events)


def run_opencode(prompt: str, *, cwd=None, env=None, timeout=None,
                 runner: Callable[..., subprocess.CompletedProcess] | None = None) -> OpenCodeResult:
    """Send *prompt* on stdin and parse all machine-readable stdout."""
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    runner = runner or subprocess.run
    completed = runner(list(OPENCODE_ARGV), input=prompt, text=True,
                       capture_output=True, cwd=cwd, env=env, timeout=timeout,
                       check=False)
    events = parse_jsonl(completed.stdout)
    return OpenCodeResult(completed.returncode, events, completed.stdout,
                          completed.stderr, 0.0)


# Descriptive aliases make the small adapter convenient to use from the CLI
# and from fixture-driven checks without exposing a second invocation shape.
invoke_opencode = run_opencode


def _text(event: Mapping[str, Any]) -> str:
    for key in ("text", "message", "content", "body"):
        value = event.get(key)
        if isinstance(value, str):
            return value
    message = event.get("message")
    if isinstance(message, dict):
        return _text(message)
    content = event.get("content")
    if isinstance(content, list):
        return "".join(item if isinstance(item, str) else _text(item)
                       for item in content if isinstance(item, (str, dict)))
    part = event.get("part")
    if isinstance(part, dict):
        return _text(part)
    return ""


def _role(event: Mapping[str, Any]) -> str:
    for key in ("agent", "role", "author"):
        if isinstance(event.get(key), str):
            return event[key].lower()
    for key in ("message", "part"):
        if isinstance(event.get(key), dict):
            role = _role(event[key])
            if role:
                return role
    return ""


def has_single_root(events: Iterable[Mapping[str, Any]]) -> bool:
    """Return whether event session references identify exactly one root."""
    roots = set()
    for event in events:
        session = event.get("sessionID", event.get("session_id", event.get("session")))
        parent = event.get("parentID", event.get("parent_id", event.get("parentSessionID")))
        if session and not parent:
            roots.add(str(session))
    return len(roots) == 1


validate_single_root = has_single_root


_DONE = re.compile(r"^DONE$", re.MULTILINE)


def final_message_is_done(events: Sequence[Mapping[str, Any]]) -> bool:
    """Check the last textual message, rather than a substring in any output."""
    texts = [_text(event).strip() for event in events if _text(event).strip()]
    return bool(texts and _DONE.fullmatch(texts[-1]))


validate_final_done = final_message_is_done


_COMMIT = re.compile(r"^final commit:\s*[0-9a-f]{40}$", re.IGNORECASE | re.MULTILINE)


def parse_tester_report(events: Sequence[Mapping[str, Any]]) -> bool:
    """Validate the latest completed Tester report structurally.

    A report is completed only when it identifies Tester and has an anchored
    ``PASS`` line and anchored final-commit line.  Earlier reports cannot mask
    a later incomplete or failed report.
    """
    reports = []
    for event in events:
        role = _role(event)
        text = _text(event)
        if "tester" in role or str(event.get("type", "")).lower() == "tester":
            reports.append(text)
    if not reports:
        return False
    report = reports[-1]
    return bool(re.search(r"^PASS$", report, re.MULTILINE) and _COMMIT.search(report))
