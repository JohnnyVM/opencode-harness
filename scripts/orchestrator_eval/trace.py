"""Reader and conservative aggregator for OpenCode trace format 0.0.7."""

from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping


TRACE_VERSION = "0.0.7"


@dataclass(frozen=True)
class TraceReport:
    sessions: tuple[Mapping[str, Any], ...]
    model: str | None
    input_tokens: int
    output_tokens: int
    duration: float
    complete: bool
    missing: tuple[str, ...] = ()

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def discover_sessions(root: str | Path) -> tuple[Path, ...]:
    """Discover trace files recursively; nested session directories matter."""
    root = Path(root)
    if not root.exists():
        return ()
    return tuple(sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in {".jsonl", ".json"}))


find_trace_files = discover_sessions


def _records(path: Path) -> Iterable[Mapping[str, Any]]:
    if path.suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict) and "sessions" in value:
            nested = value["sessions"]
            yield from (nested.values() if isinstance(nested, dict) else nested)
        else:
            yield from (value if isinstance(value, list) else [value])
    else:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    yield value


def read_trace(root: str | Path) -> tuple[Mapping[str, Any], ...]:
    """Read every 0.0.7 trace record below *root*."""
    records = []
    for path in discover_sessions(root):
        for record in _records(path):
            version = record.get("version", record.get("traceVersion"))
            if version is not None and str(version) != TRACE_VERSION:
                raise ValueError(f"unsupported trace version: {version}")
            records.append(record)
    return tuple(records)


def aggregate_trace(root: str | Path) -> TraceReport:
    sessions: list[Mapping[str, Any]] = []
    models: set[str] = set()
    input_tokens = output_tokens = 0
    starts: list[float] = []
    ends: list[float] = []
    malformed_tokens = False
    for record in read_trace(root):
        sessions.append(record)
        payload: Mapping[str, Any] = (record["data"] if isinstance(record.get("data"), dict) else record)
        model = (payload.get("model") or payload.get("modelID") or
                 (record.get("model") if isinstance(record.get("model"), str) else None))
        if model:
            models.add(str(model))
        # ``usage`` is authoritative.  Top-level aliases are only a fallback
        # for records which do not expose that object; otherwise counting both
        # representations would inflate the total.
        usage_key = "usage" if "usage" in payload else ("tokens" if "tokens" in payload else None)
        usage = payload.get(usage_key) if usage_key else None
        token_source = usage if isinstance(usage, dict) else ({} if usage_key else payload)
        in_value, in_bad = _token_value(token_source, ("input", "prompt", "inputTokens"))
        out_value, out_bad = _token_value(token_source, ("output", "completion", "outputTokens"))
        malformed_tokens |= in_bad or out_bad or (usage_key is not None and not isinstance(usage, dict))
        input_tokens += in_value
        output_tokens += out_value
        for key, target in (("start", starts), ("startedAt", starts), ("timestamp", starts)):
            if key in payload:
                value = _time(payload[key])
                if value is not None: target.append(value); break
        for key, target in (("end", ends), ("endedAt", ends), ("completedAt", ends)):
            if key in payload:
                value = _time(payload[key])
                if value is not None: target.append(value); break
    missing = []
    if not models:
        missing.append("model")
    elif len(models) > 1:
        missing.append("model-conflict")
    if not sessions:
        missing.append("sessions")
    if input_tokens + output_tokens == 0:
        missing.append("tokens")
    if malformed_tokens:
        missing.append("malformed-tokens")
    duration = max(ends) - min(starts) if starts and ends else 0.0
    if not duration:
        for record in sessions:
            payload: Mapping[str, Any] = (record["data"] if isinstance(record.get("data"), dict) else record)
            if isinstance(payload, dict) and isinstance(payload.get("duration_ms"), (int, float)):
                duration += float(payload["duration_ms"]) / 1000
    if duration <= 0:
        missing.append("timing")
    return TraceReport(tuple(sessions), next(iter(models)) if len(models) == 1 else None,
                       input_tokens, output_tokens, duration, not missing, tuple(missing))


parse_trace = aggregate_trace
aggregate = aggregate_trace


def _time(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def _token_value(source: Mapping[str, Any], names: tuple[str, ...]) -> tuple[int, bool]:
    """Return one token field, and flag present-but-invalid numeric evidence."""
    value = next((source[name] for name in names if name in source), 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0, any(name in source for name in names)
    if not math.isfinite(float(value)) or value < 0:
        return 0, True
    return int(value), False
