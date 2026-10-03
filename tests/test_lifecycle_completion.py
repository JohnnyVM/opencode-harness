"""Incomplete primary sessions must not advance the lifecycle."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import lifecycle_opencode


class LifecycleCompletionTests(unittest.TestCase):
    def capture(self, root, finish, text, error=None):
        commands = []
        payload = {
            "info": {"id": "root", "agent": "architect"},
            "messages": [{
                "info": {"role": "assistant", "agent": "architect", "finish": finish},
                "parts": [{"type": "text", "text": text}],
            }],
        }
        if error:
            payload["messages"][0]["parts"].append({
                "type": "tool", "tool": "glob", "state": {"status": "error", "error": error},
            })

        def execute(command, **kwargs):
            commands.append(command)
            if command[1] == "run":
                agent = command[command.index("--agent") + 1]
                payload["info"]["agent"] = agent
                payload["messages"][0]["info"]["agent"] = agent
                kwargs["stdout"].write(json.dumps({"type": "step_finish", "sessionID": "root"}) + "\n")
                kwargs["stdout"].flush()
            elif command[1:3] == ["session", "list"]:
                kwargs["stdout"].write(b"[]")
            elif command[1] == "export":
                kwargs["stdout"].write(json.dumps(payload).encode())
            return subprocess.CompletedProcess(command, 0)

        with patch.object(lifecycle_opencode, "_require_executable", return_value="opencode"), \
             patch.object(lifecycle_opencode.subprocess, "run", side_effect=execute):
            lifecycle_opencode.capture_agents(root, root / "artifacts", root, [
                {"stage": "architecture", "agent": "architect", "prompt": "spec.md"},
                {"stage": "implementation", "agent": "implementation-orchestrator", "prompt": "arch.md",
                 "session": "root"},
            ])
        return commands

    def test_tool_rejection_stops_before_next_stage_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(RuntimeError, "architecture: architect did not complete.*rejected permission"):
                self.capture(root, "tool-calls", "", "The user rejected permission")
            stage = root / "artifacts/architecture"
            self.assertTrue((stage / "events.jsonl").is_file())
            self.assertTrue((stage / "sessions/root.json").is_file())
            self.assertFalse((root / "artifacts/implementation").exists())

    def test_stop_without_final_text_is_not_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "no final text response"):
                self.capture(Path(temp), "stop", "")

    def test_final_reply_allows_next_stage_and_runtime_logs_are_enabled(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            commands = self.capture(root, "stop", "Stage completed.")
            runs = [command for command in commands if command[1] == "run"]
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[1][runs[1].index("--session") + 1], "root")
            for command in runs:
                self.assertIn("--print-logs", command)
                self.assertEqual(command[command.index("--log-level") + 1], "INFO")
            self.assertTrue((root / "artifacts/implementation/events.jsonl").exists())
            self.assertTrue((root / "artifacts/metrics.json").is_file())


if __name__ == "__main__":
    unittest.main()
