"""Model selection reaches lifecycle phases and OpenCode agent configuration."""

import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import lifecycle_opencode, run_tests


class LifecycleModelTests(unittest.TestCase):
    def test_model_id_rejects_invalid_values(self):
        for value in ("", "model", "/model", "provider/", "provider/model name"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                run_tests.model_id(value)
        self.assertEqual(run_tests.model_id("provider/model"), "provider/model")

    def test_report_requires_each_package_ticket(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "package.md"
            package.write_text("## Tickets and Dependencies\n### T1 — First\n### T2 — Second\n")
            sessions = root / "implementation" / "sessions"
            sessions.mkdir(parents=True)
            report = ("## Outcome and Stopping Point\nStopped in IMPLEMENTING.\n"
                      "## Ticket Ledger\n- T1: partial — src/one.py\n"
                      "- T2: not started — dependency T1\n"
                      "## Verification\nTester not run.\n"
                      "## Blocker and Causal Chain\nT1 blocked T2.\n"
                      "## Remaining Work and Safest Next Action\nFinish T1 then run Tester.\n")
            session = {"messages": [
                {"info": {"role": "user", "agent": "implementation-orchestrator"}},
                {"info": {"role": "assistant", "agent": "implementation-orchestrator"},
                 "parts": [{"type": "text", "text": report}]},
            ]}
            path = sessions / "root.json"
            path.write_text(json.dumps(session))
            lifecycle_opencode.validate_implementation_report(root, package)
            session["messages"][1]["parts"][0]["text"] = report.replace(
                "- T2: not started — dependency T1\n", ""
            )
            path.write_text(json.dumps(session))
            with self.assertRaisesRegex(AssertionError, "ticket ledger"):
                lifecycle_opencode.validate_implementation_report(root, package)

    def test_mcp_name_rejects_unknown_servers(self):
        self.assertEqual(run_tests.mcp_name("ripwire"), "ripwire")
        with self.assertRaises(argparse.ArgumentTypeError):
            run_tests.mcp_name("unknown")

    def test_cleanup_artifacts_removes_only_selected_tests(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            selected = root / "tests" / "selected"
            selected.mkdir(parents=True)
            unselected = root / "tests" / "unselected"
            unselected.mkdir()
            selected_artifacts = root / "artifacts" / selected.name / "previous-run"
            selected_artifacts.mkdir(parents=True)
            unselected_artifacts = root / "artifacts" / unselected.name / "previous-run"
            unselected_artifacts.mkdir(parents=True)

            with patch.object(run_tests, "ROOT", root):
                run_tests.cleanup_artifacts([selected])

            self.assertFalse(selected_artifacts.parent.exists())
            self.assertTrue(unselected_artifacts.is_dir())

    def test_runner_passes_overrides_to_each_phase(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            test = root / "sample"
            test.mkdir()
            for phase in run_tests.PHASES:
                (test / phase).write_text(
                    "import os\n"
                    "from pathlib import Path\n"
                    "Path(os.environ['TEST_WORKSPACE'], '" + phase + "').write_text("
                    "os.environ.get('TEST_SPEC_MODEL', '') + '|' + "
                    "os.environ.get('TEST_CODER_HEAVY_MODEL', ''))\n"
                )
            workspace = root / "workspace"
            workspace.mkdir()
            with patch.dict(os.environ, {"TEST_CODER_HEAVY_MODEL": "stale/model"}):
                self.assertTrue(run_tests.run_test(test, workspace, root / "artifacts", {
                    "models": {
                        "spec_model": "acme/spec",
                        "coder_heavy_model": "acme/heavy",
                    },
                }))
            for phase in run_tests.PHASES:
                self.assertEqual((workspace / phase).read_text(), "acme/spec|acme/heavy")
            self.assertTrue(run_tests.run_test(test, workspace, root / "artifacts"))
            for phase in run_tests.PHASES:
                self.assertEqual((workspace / phase).read_text(), "|")

    def test_runner_passes_mcp_selections_to_each_phase(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            test = root / "sample"
            test.mkdir()
            for phase in run_tests.PHASES:
                (test / phase).write_text(
                    "import os\n"
                    "from pathlib import Path\n"
                    "Path(os.environ['TEST_WORKSPACE'], '" + phase + "').write_text("
                    "os.environ['TEST_ENABLED_MCPS'] + '|' + os.environ['TEST_DISABLED_MCPS'])\n"
                )
            workspace = root / "workspace"
            workspace.mkdir()
            self.assertTrue(run_tests.run_test(
                test, workspace, root / "artifacts", {
                    "enabled_mcps": ("ripwire",),
                    "disabled_mcps": ("playwright",),
                },
            ))
            for phase in run_tests.PHASES:
                self.assertEqual((workspace / phase).read_text(), "ripwire|playwright")
            self.assertTrue(run_tests.run_test(test, workspace, root / "artifacts"))
            for phase in run_tests.PHASES:
                self.assertEqual((workspace / phase).read_text(), "|")

    def test_config_overrides_named_agents_without_erasing_permissions(self):
        overrides = {
            "TEST_SPEC_MODEL": "acme/spec",
            "TEST_IMPLEMENTATION_MODEL": "acme/implementation",
            "TEST_CODER_LIGHT_MODEL": "acme/light",
            "TEST_CODER_HEAVY_MODEL": "acme/heavy",
        }
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, overrides):
            root = Path(temp)
            captured = {}

            def intercept(command, **kwargs):
                captured.update(command=command, environment=kwargs["env"])
                raise RuntimeError("stopped before OpenCode starts")

            with patch.object(lifecycle_opencode, "_require_executable", return_value="opencode"), \
                 patch.object(lifecycle_opencode.subprocess, "run", side_effect=intercept), \
                 self.assertRaisesRegex(RuntimeError, "stopped before OpenCode starts"):
                lifecycle_opencode.capture_agents(root, root / "artifacts", root, [
                    {"stage": "implementation", "agent": "spec-orchestrator",
                     "command": "implement", "prompt": "package.md"},
                ])
            config = json.loads(captured["environment"]["OPENCODE_CONFIG_CONTENT"])
            self.assertEqual({agent: config["agent"][agent]["model"]
                              for agent in lifecycle_opencode.MODEL_ENV}, {
                "spec-orchestrator": "acme/spec",
                "implementation-orchestrator": "acme/implementation",
                "coder-light": "acme/light",
                "coder-heavy": "acme/heavy",
            })
            self.assertIn("permission", config["agent"]["implementation-orchestrator"])
            self.assertEqual(captured["command"][-3:], ["--command", "implement", "package.md"])
            self.assertEqual(lifecycle_opencode.expected_primary_models(),
                             ("acme/spec", "acme/implementation"))

    def test_config_applies_selected_mcps(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ,
            {
                lifecycle_opencode.ENABLED_MCPS_ENV: "ripwire",
                lifecycle_opencode.DISABLED_MCPS_ENV: "playwright",
            },
        ):
            root = Path(temp)
            captured = {}

            def intercept(command, **kwargs):
                captured.update(environment=kwargs["env"])
                raise RuntimeError("stopped before OpenCode starts")

            with patch.object(lifecycle_opencode, "_require_executable", return_value="opencode"), \
                 patch.object(lifecycle_opencode.subprocess, "run", side_effect=intercept), \
                 self.assertRaisesRegex(RuntimeError, "stopped before OpenCode starts"):
                lifecycle_opencode.capture_agents(root, root / "artifacts", root, [
                    {"stage": "sample", "agent": "spec-orchestrator", "prompt": "test"},
                ])
            config = json.loads(captured["environment"]["OPENCODE_CONFIG_CONTENT"])
            self.assertTrue(config["mcp"]["ripwire"]["enabled"])
            self.assertFalse(config["mcp"]["playwright"]["enabled"])

    def test_unspecified_models_keep_defaults(self):
        with patch.dict(os.environ, {key: "" for key in lifecycle_opencode.MODEL_ENV.values()}):
            self.assertEqual(lifecycle_opencode.selected_models(), {})
            self.assertEqual(lifecycle_opencode.expected_primary_models(),
                             ("openai/gpt-6-sol", "openai/gpt-6-luna"))

    def test_validation_detects_wrong_coder_model_when_invoked(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"TEST_CODER_LIGHT_MODEL": "acme/light"}
        ):
            artifacts = Path(temp)
            stages = []
            for stage, agent, model in (
                ("spec-orchestrator", "spec-orchestrator", "openai/gpt-6-sol"),
                ("implementation", "implementation-orchestrator", "openai/gpt-6-luna"),
                ("implementation", "coder-light", "wrong/model"),
            ):
                session_id = agent
                session = {"id": session_id, "agent": agent, "model": model,
                           "tokens": {"input": 1, "output": 1}, "cost": 0}
                stage_dir = artifacts / stage / "sessions"
                stage_dir.mkdir(parents=True, exist_ok=True)
                (stage_dir / f"{session_id}.json").write_text(json.dumps({
                    "info": {"id": session_id, "tokens": session["tokens"], "cost": 0}
                }))
                if not stages or stages[-1]["stage"] != stage:
                    stages.append({"stage": stage, "elapsed_seconds": 1, "sessions": []})
                stages[-1]["sessions"].append(session)
            (artifacts / "metrics.json").write_text(json.dumps({
                "stages": stages,
                "totals": {"tokens": {"input": 3, "output": 3, "reasoning": 0,
                                      "cache_read": 0, "cache_write": 0}, "cost": 0,
                           "elapsed_seconds": 2},
                "opencode_trace": {"initialized": True, "records": 0, "models": []},
            }))
            (artifacts / "opencode-trace").mkdir()
            with self.assertRaisesRegex(AssertionError, "coder-light used.*wrong/model"):
                lifecycle_opencode.validate_observability(
                    artifacts, ("spec-orchestrator", "implementation"),
                    lifecycle_opencode.expected_primary_models(),
                )
            stages[-1]["sessions"][-1]["model"] = "acme/light"
            (artifacts / "metrics.json").write_text(json.dumps({
                **json.loads((artifacts / "metrics.json").read_text()), "stages": stages
            }))
            lifecycle_opencode.validate_observability(
                artifacts, ("spec-orchestrator", "implementation"),
                lifecycle_opencode.expected_primary_models(),
            )


if __name__ == "__main__":
    unittest.main()
