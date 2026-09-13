"""Private, atomic evaluation artifacts. JSON is the source of truth."""

import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping


def markdown_report(result: Mapping[str, Any]) -> str:
    outcome = result.get("outcome", result.get("status", "UNKNOWN"))
    lines = [f"# Evaluation: {outcome}", ""]
    for key in ("case_id", "model", "duration", "timings"):
        if key in result:
            lines.append(f"- **{key}:** {result[key]}")
    checks = result.get("checks", result.get("results"))
    if checks is not None:
        lines.extend(("", "## Checks", "", "```json", json.dumps(checks, indent=2, sort_keys=True), "```"))
    return "\n".join(lines) + "\n"


def _atomic(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_report(directory: Path, result: Mapping[str, Any], *, raw: str | None = None) -> tuple[Path, Path]:
    """Write private JSON and markdown, with markdown derived from that JSON."""
    directory = Path(directory)
    payload = json.dumps(dict(result), indent=2, sort_keys=True) + "\n"
    json_path, markdown_path = directory / "result.json", directory / "result.md"
    _atomic(json_path, payload)
    authoritative = json.loads(json_path.read_text(encoding="utf-8"))
    _atomic(markdown_path, markdown_report(authoritative))
    if raw is not None:
        _atomic(directory / "raw.jsonl", raw)
    return json_path, markdown_path


write_artifacts = write_report
