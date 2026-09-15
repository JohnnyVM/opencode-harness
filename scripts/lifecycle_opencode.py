"""Capture OpenCode lifecycle sessions and validate their observability data."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


PLUGIN = "opencode-trace@0.3.1"


def _require_executable(name):
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"{name} is not installed")
    return path


def _event_session_ids(path):
    session_ids = set()
    for line in path.read_text().splitlines():
        session_id = json.loads(line).get("sessionID")
        if session_id:
            session_ids.add(session_id)
    return session_ids


def _child_session_ids(value):
    session_ids = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "sessionId" and isinstance(item, str):
                session_ids.add(item)
            session_ids.update(_child_session_ids(item))
    elif isinstance(value, list):
        for item in value:
            session_ids.update(_child_session_ids(item))
    return session_ids


def capture_agents(repository, artifacts, harness, invocations):
    """Run agent invocations and persist raw sessions, traces, and metrics."""
    opencode = _require_executable("opencode")
    environment = os.environ.copy()
    environment.update(
        {
            "OPENCODE_CONFIG": str(harness / "opencode" / "opencode.jsonc"),
            "OPENCODE_CONFIG_DIR": str(harness / "opencode"),
            "OPENCODE_CONFIG_CONTENT": json.dumps(
                {
                    "mcp": {"playwright": {"enabled": False}},
                    "plugin": [PLUGIN],
                }
            ),
            "OPENCODE_DISABLE_MODELS_FETCH": "1",
            "OPENCODE_DISABLE_LSP_DOWNLOAD": "1",
        }
    )

    def export_sessions(stage_dir, started_ms, ended_ms, root_ids, stderr):
        index_path = stage_dir / "sessions-index.json"
        with index_path.open("wb") as output:
            subprocess.run(
                [opencode, "session", "list", "--format", "json", "-n", "200"],
                cwd=repository,
                env=environment,
                stdout=output,
                stderr=stderr,
                check=True,
            )
        session_ids = set(root_ids)
        for session in json.loads(index_path.read_text()):
            created = session.get("created", 0)
            if (
                started_ms - 2000 <= created <= ended_ms + 5000
                and session.get("directory") == str(repository)
            ):
                session_ids.add(session["id"])

        sessions = []
        reasoning = []
        sessions_dir = stage_dir / "sessions"
        sessions_dir.mkdir()
        exported_ids = set()
        while session_ids - exported_ids:
            session_id = sorted(session_ids - exported_ids)[0]
            exported_ids.add(session_id)
            session_path = sessions_dir / f"{session_id}.json"
            with session_path.open("wb") as output:
                subprocess.run(
                    [opencode, "export", session_id],
                    cwd=repository,
                    env=environment,
                    stdout=output,
                    stderr=stderr,
                    check=True,
                )
            payload = json.loads(session_path.read_text())
            session_ids.update(_child_session_ids(payload))
            info = payload["info"]
            model = info.get("model") or {}
            sessions.append(
                {
                    "id": info["id"],
                    "agent": info.get("agent"),
                    "model": "/".join(
                        value
                        for value in (model.get("providerID"), model.get("id"))
                        if value
                    ),
                    "cost": info.get("cost", 0),
                    "tokens": info.get("tokens", {}),
                    "time": info.get("time", {}),
                }
            )
            for message in payload.get("messages", []):
                message_info = message.get("info", {})
                for part in message.get("parts", []):
                    if part.get("type") == "reasoning":
                        reasoning.append(
                            {
                                "sessionID": session_id,
                                "messageID": message_info.get("id"),
                                "modelID": message_info.get("modelID"),
                                "providerID": message_info.get("providerID"),
                                "part": part,
                            }
                        )

        with (stage_dir / "reasoning.jsonl").open("w") as stream:
            for part in reasoning:
                stream.write(json.dumps(part) + "\n")
        return sessions

    def run_agent(invocation):
        stage_dir = artifacts / invocation["stage"]
        stage_dir.mkdir(parents=True)
        events = stage_dir / "events.jsonl"
        command = [
            opencode,
            "run",
            "--agent",
            invocation["agent"],
            "--format",
            "json",
            "--thinking",
            "--dir",
            str(repository),
            invocation["prompt"],
        ]
        for path in invocation.get("files", ()):
            command.extend(("--file", str(path)))

        started_ms = int(time.time() * 1000)
        started = time.monotonic()
        with events.open("w") as output, (stage_dir / "stderr.log").open("w") as stderr:
            result = subprocess.run(
                command,
                cwd=repository,
                env=environment,
                stdout=output,
                stderr=stderr,
                check=False,
            )
            elapsed = time.monotonic() - started
            ended_ms = int(time.time() * 1000)
            sessions = export_sessions(
                stage_dir,
                started_ms,
                ended_ms,
                _event_session_ids(events),
                stderr,
            )
        if result.returncode:
            raise subprocess.CalledProcessError(result.returncode, result.args)
        responses = [
            json.loads(line).get("part", {}).get("text", "")
            for line in events.read_text().splitlines()
        ]
        return {
            "stage": invocation["stage"],
            "agent": invocation["agent"],
            "elapsed_seconds": elapsed,
            "blocked": any("BLOCKED_" in response for response in responses),
            "sessions": sessions,
        }

    artifacts.mkdir(parents=True, exist_ok=True)
    stages = [run_agent(invocation) for invocation in invocations]
    totals = {
        "cost": 0,
        "tokens": {
            "input": 0,
            "output": 0,
            "reasoning": 0,
            "cache_read": 0,
            "cache_write": 0,
        },
        "elapsed_seconds": sum(stage["elapsed_seconds"] for stage in stages),
    }
    for stage in stages:
        for session in stage["sessions"]:
            tokens = session["tokens"]
            cache = tokens.get("cache", {})
            totals["cost"] += session["cost"]
            totals["tokens"]["input"] += tokens.get("input", 0)
            totals["tokens"]["output"] += tokens.get("output", 0)
            totals["tokens"]["reasoning"] += tokens.get("reasoning", 0)
            totals["tokens"]["cache_read"] += cache.get("read", 0)
            totals["tokens"]["cache_write"] += cache.get("write", 0)

    trace_source = repository / ".agent-trace"
    trace_records = []
    if trace_source.is_dir():
        for path in trace_source.glob("*traces.jsonl"):
            trace_records.extend(json.loads(line) for line in path.read_text().splitlines())
        shutil.copytree(trace_source, artifacts / "opencode-trace", dirs_exist_ok=True)
    trace_models = sorted(
        {
            conversation.get("contributor", {}).get("model_id")
            for record in trace_records
            for file in record["files"]
            for conversation in file["conversations"]
            if conversation.get("contributor", {}).get("model_id")
        }
    )
    (artifacts / "metrics.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "stages": stages,
                "totals": totals,
                "opencode_trace": {
                    "initialized": (trace_source / ".gitignore").is_file(),
                    "records": len(trace_records),
                    "models": trace_models,
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Observability artifacts: {artifacts}")


def validate_observability(artifacts, expected_stages, expected_models):
    """Sanity-check metrics against raw exports and return blocked stages."""
    metrics = json.loads((artifacts / "metrics.json").read_text())
    if [stage["stage"] for stage in metrics["stages"]] != list(expected_stages):
        raise AssertionError("metrics do not contain the expected agent stages")
    if any(stage["elapsed_seconds"] <= 0 for stage in metrics["stages"]):
        raise AssertionError("agent elapsed times must be positive")
    sessions = [session for stage in metrics["stages"] for session in stage["sessions"]]
    models = {session["model"] for session in sessions}
    if not set(expected_models).issubset(models):
        raise AssertionError(f"missing expected models: {sorted(set(expected_models) - models)}")
    tokens = metrics["totals"]["tokens"]
    if tokens["input"] <= 0 or tokens["output"] <= 0:
        raise AssertionError(f"invalid token totals: {tokens}")
    if metrics["totals"]["cost"] < 0:
        raise AssertionError("total model cost cannot be negative")

    exported_sessions = [
        json.loads(path.read_text())["info"]
        for stage in expected_stages
        for path in (artifacts / stage / "sessions").glob("*.json")
    ]
    if {session["id"] for session in exported_sessions} != {
        session["id"] for session in sessions
    }:
        raise AssertionError("metrics do not include every exported session")
    recomputed_tokens = {
        "input": sum(session.get("tokens", {}).get("input", 0) for session in exported_sessions),
        "output": sum(session.get("tokens", {}).get("output", 0) for session in exported_sessions),
        "reasoning": sum(
            session.get("tokens", {}).get("reasoning", 0) for session in exported_sessions
        ),
        "cache_read": sum(
            session.get("tokens", {}).get("cache", {}).get("read", 0)
            for session in exported_sessions
        ),
        "cache_write": sum(
            session.get("tokens", {}).get("cache", {}).get("write", 0)
            for session in exported_sessions
        ),
    }
    if tokens != recomputed_tokens:
        raise AssertionError("token totals do not match the raw session exports")
    if metrics["totals"]["cost"] != sum(
        session.get("cost", 0) for session in exported_sessions
    ):
        raise AssertionError("cost total does not match the raw session exports")

    trace_paths = sorted((artifacts / "opencode-trace").glob("*traces.jsonl"))
    trace_records = [
        json.loads(line)
        for path in trace_paths
        for line in path.read_text().splitlines()
    ]
    trace_models = {
        conversation.get("contributor", {}).get("model_id")
        for record in trace_records
        for file in record["files"]
        for conversation in file["conversations"]
    }
    trace_models.discard(None)
    trace_metrics = metrics["opencode_trace"]
    if not trace_metrics["initialized"]:
        raise AssertionError("opencode-trace did not initialize")
    if trace_records and not trace_models:
        raise AssertionError("opencode-trace records have no AI model attribution")
    if (
        len(trace_records) != trace_metrics["records"]
        or sorted(trace_models) != trace_metrics["models"]
    ):
        raise AssertionError("opencode-trace metrics do not match the raw records")

    print(
        "Model metrics: "
        f"models={sorted(models)}, tokens={tokens}, cost={metrics['totals']['cost']}, "
        f"elapsed={metrics['totals']['elapsed_seconds']:.2f}s, "
        f"trace_records={len(trace_records)}"
    )
    print(f"Raw artifacts: {artifacts}")
    return [stage["stage"] for stage in metrics["stages"] if stage["blocked"]]
