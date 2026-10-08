"""Model selection reaches lifecycle phases and OpenCode agent configuration."""

import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import lifecycle_opencode, run_tests
from tests.test_coder_assignment_gate import ASSIGNMENT


def write_session(root, stage, payload, name="root"):
    sessions = root / stage / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    path = sessions / f"{name}.json"
    path.write_text(json.dumps(payload))
    return path


class LifecycleModelTests(unittest.TestCase):
    def test_exported_coder_assignments_are_revalidated(self):
        with tempfile.TemporaryDirectory() as temp:
            artifacts = Path(temp)
            payload = {"messages": [{
                "info": {"role": "user", "agent": "coder-medium"},
                "parts": [{"type": "text", "text": "Implement this ticket.\n\n" + ASSIGNMENT}],
            }]}
            path = write_session(artifacts, "implementation", payload, "coder")
            lifecycle_opencode.validate_coder_assignments(artifacts)
            payload["messages"][0]["parts"][0]["text"] = "status: ASSIGNMENT_READY\nTODO"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(AssertionError, "invalid Coder Assignment"):
                lifecycle_opencode.validate_coder_assignments(artifacts)

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
            report = ("## Outcome and Stopping Point\nStatus: DONE — all gates passed.\n"
                      "## Ticket Ledger\n- T1: completed — src/one.py\n"
                      "- T2: completed — src/two.py\n"
                      "## Verification\n- **Tester gate:** `PASS`.\n"
                      "Code Reviewer: APPROVED\n"
                      "## Blocker and Causal Chain\nNone.\n"
                      "## Remaining Work and Safest Next Action\nNone.\n")
            session = {"messages": [
                {"info": {"role": "user", "agent": "implementation-orchestrator"}},
                {"info": {"role": "assistant", "agent": "implementation-orchestrator"},
                 "parts": [{"type": "text", "text": report}]},
            ]}
            path = write_session(root, "implementation", session)
            lifecycle_opencode.validate_implementation_report(root, package)
            lifecycle_opencode.validate_implementation_report(root, package, expected_status="DONE")
            session["messages"][1]["parts"][0]["text"] = report.replace(
                "T1: completed", "**T1: completed**"
            ).replace("T2: completed", "**T2: completed**")
            path.write_text(json.dumps(session))
            lifecycle_opencode.validate_implementation_report(root, package, expected_status="DONE")
            session["messages"][1]["parts"][0]["text"] = report.replace("`PASS`", "`FAIL`")
            path.write_text(json.dumps(session))
            with self.assertRaisesRegex(AssertionError, "Tester PASS"):
                lifecycle_opencode.validate_implementation_report(root, package, expected_status="DONE")
            session["messages"][1]["parts"][0]["text"] = report.replace(
                "Code Reviewer: APPROVED", "Code Reviewer: CHANGES_REQUIRED"
            )
            path.write_text(json.dumps(session))
            with self.assertRaisesRegex(AssertionError, "Code Reviewer approval"):
                lifecycle_opencode.validate_implementation_report(root, package, expected_status="DONE")
            session["messages"][1]["parts"][0]["text"] = report.replace(
                "T2: completed", "T2: partial"
            )
            path.write_text(json.dumps(session))
            with self.assertRaisesRegex(AssertionError, "incomplete tickets"):
                lifecycle_opencode.validate_implementation_report(root, package, expected_status="DONE")
            session["messages"][1]["parts"][0]["text"] = report.replace(
                "- T2: completed — src/two.py\n", ""
            )
            path.write_text(json.dumps(session))
            with self.assertRaisesRegex(AssertionError, "ticket ledger"):
                lifecycle_opencode.validate_implementation_report(root, package)
            session["messages"][1]["parts"][0]["text"] = report.replace(
                "Status: DONE — all gates passed.", "Did not reach **DONE**."
            )
            path.write_text(json.dumps(session))
            with self.assertRaisesRegex(AssertionError, "did not finish with DONE"):
                lifecycle_opencode.validate_implementation_report(
                    root, package, expected_status="DONE"
                )

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
                    "os.environ.get('TEST_CODER_MEDIUM_MODEL', '') + '|' + "
                    "os.environ.get('TEST_CODER_HEAVY_MODEL', ''))\n"
                )
            workspace = root / "workspace"
            workspace.mkdir()
            with patch.dict(os.environ, {
                "TEST_CODER_MEDIUM_MODEL": "stale/medium",
                "TEST_CODER_HEAVY_MODEL": "stale/heavy",
            }):
                self.assertTrue(run_tests.run_test(test, workspace, root / "artifacts", {
                    "models": {
                        "spec_model": "acme/spec",
                        "coder_medium_model": "acme/medium",
                        "coder_heavy_model": "acme/heavy",
                    },
                }))
            for phase in run_tests.PHASES:
                self.assertEqual((workspace / phase).read_text(), "acme/spec|acme/medium|acme/heavy")
            self.assertTrue(run_tests.run_test(test, workspace, root / "artifacts"))
            for phase in run_tests.PHASES:
                self.assertEqual((workspace / phase).read_text(), "||")

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
            "TEST_ARCHITECT_MODEL": "acme/architect",
            "TEST_IMPLEMENTATION_MODEL": "acme/implementation",
            "TEST_CODER_LIGHT_MODEL": "acme/light",
            "TEST_CODER_MEDIUM_MODEL": "acme/medium",
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
                "architect": "acme/architect",
                "implementation-orchestrator": "acme/implementation",
                "coder-light": "acme/light",
                "coder-medium": "acme/medium",
                "coder-heavy": "acme/heavy",
            })
            self.assertIn("permission", config["agent"]["implementation-orchestrator"])
            self.assertEqual(
                config["agent"]["spec-orchestrator"]["permission"]["external_directory"]
                [str(root / "opencode/**")], "allow"
            )
            self.assertEqual(
                config["agent"]["spec-orchestrator"]["permission"]["bash"]
                [f"python3 {root / 'opencode/scripts/validate_specification_package.py'}*"],
                "allow",
            )
            self.assertEqual(
                config["agent"]["architect"]["permission"]["bash"]
                [f"python3 {root / 'opencode/scripts/validate_architecture_package.py'}*"],
                "allow",
            )
            self.assertEqual(captured["command"][-3:], ["--command", "implement", "package.md"])
            self.assertEqual(config["agent"]["architect"]["model"], "acme/architect")
            self.assertEqual(
                config["agent"]["architect"]["permission"]["external_directory"]
                [str(Path.home() / ".config/opencode/**")], "allow"
            )
            self.assertEqual(lifecycle_opencode.expected_primary_models(),
                             ("acme/spec", "acme/architect", "acme/implementation"))

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
                             ("openai/gpt-6.1-sol", "openai/gpt-6.1-sol", "openai/gpt-6-luna"))
            self.assertEqual(lifecycle_opencode.DEFAULT_MODELS["coder-medium"],
                             "openai/gpt-6-luna")

    def test_validation_detects_wrong_coder_model_when_invoked(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {
                "TEST_ARCHITECT_MODEL": "acme/architect",
                "TEST_CODER_LIGHT_MODEL": "acme/light",
                "TEST_CODER_MEDIUM_MODEL": "acme/medium",
            }
        ):
            artifacts = Path(temp)
            stages = []
            for stage, agent, model in (
                ("specification", "spec-orchestrator", "openai/gpt-6.1-sol"),
                ("architecture", "architect", "wrong/architect"),
                ("implementation", "implementation-orchestrator", "openai/gpt-6-luna"),
                ("implementation", "coder-light", "wrong/model"),
                ("implementation", "coder-medium", "wrong/medium"),
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
                "totals": {"tokens": {"input": 5, "output": 5, "reasoning": 0,
                                      "cache_read": 0, "cache_write": 0}, "cost": 0,
                           "elapsed_seconds": 2},
                "opencode_trace": {"initialized": True, "records": 0, "models": []},
            }))
            (artifacts / "opencode-trace").mkdir()
            with self.assertRaisesRegex(AssertionError, "missing expected models.*acme/architect"):
                lifecycle_opencode.validate_observability(
                    artifacts, ("specification", "architecture", "implementation"),
                    lifecycle_opencode.expected_primary_models(),
                )
            stages[1]["sessions"][0]["model"] = "acme/architect"
            for session, expected in zip(stages[-1]["sessions"][1:], ("acme/light", "acme/medium")):
                (artifacts / "metrics.json").write_text(json.dumps({
                    **json.loads((artifacts / "metrics.json").read_text()), "stages": stages
                }))
                with self.assertRaisesRegex(AssertionError, f"{session['agent']} used.*wrong/"):
                    lifecycle_opencode.validate_observability(
                        artifacts, ("specification", "architecture", "implementation"),
                        lifecycle_opencode.expected_primary_models(),
                    )
                session["model"] = expected
            (artifacts / "metrics.json").write_text(json.dumps({
                **json.loads((artifacts / "metrics.json").read_text()), "stages": stages
            }))
            lifecycle_opencode.validate_observability(
                artifacts, ("specification", "architecture", "implementation"),
                lifecycle_opencode.expected_primary_models(),
            )


if __name__ == "__main__":
    unittest.main()
