"""The command hook must validate both sources before handing text to the agent."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "opencode" / "plugins" / "implement.js"
spec = importlib.util.spec_from_file_location(
    "validator_tests", ROOT / "tests" / "test_validate_implementation_package.py"
)
assert spec is not None and spec.loader is not None
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)

RUN_HOOK = """
import { pathToFileURL } from "node:url";
const { default: plugin } = await import(pathToFileURL(process.argv[1]).href);
const hook = (await plugin({ directory: process.cwd() }))["command.execute.before"];
const parts = [{ type: "text", text: "placeholder" }];
try {
  await hook({ command: "implement", arguments: process.argv[2] }, { parts });
  process.stdout.write(JSON.stringify(parts));
} catch (error) {
  process.stderr.write(error.message);
  process.exitCode = 1;
}
"""


class ImplementCommandTests(unittest.TestCase):
    def test_opencode_plugin_has_only_one_entrypoint(self):
        result = subprocess.run(
            ["node", "--input-type=module", "-e",
             "import { pathToFileURL } from 'node:url'; "
             "const plugin = await import(pathToFileURL(process.argv[1]).href); "
             "process.stdout.write(JSON.stringify(Object.keys(plugin)));", str(PLUGIN)],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ["default"])

    def issue_environment(self, directory, issue_body):
        env = os.environ.copy()
        bin_dir = directory / "bin"
        bin_dir.mkdir(exist_ok=True)
        gh = bin_dir / "gh"
        gh.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "assert sys.argv[1:] == ['issue', 'view', '42', '--repo', 'acme/widget', '--json', 'body']\n"
            "print(json.dumps({'body': os.environ['FAKE_ISSUE_BODY']}))\n"
        )
        gh.chmod(0o755)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        env["FAKE_ISSUE_BODY"] = issue_body
        return env

    def run_hook(self, source, directory, *, issue_body=None):
        env = self.issue_environment(directory, issue_body) if issue_body is not None else os.environ.copy()
        return subprocess.run(
            ["node", "--input-type=module", "-e", RUN_HOOK, str(PLUGIN), source],
            cwd=directory, env=env, text=True, capture_output=True, check=False,
        )

    def test_file_package_replaces_prompt_exactly(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = "package with spaces;$(false).md"
            (directory / source).write_text(fixture.PACKAGE)
            result = self.run_hook(source, directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), [{"type": "text", "text": fixture.PACKAGE}])

    def test_github_issue_package_replaces_prompt_exactly(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_hook("acme/widget#42", Path(temp), issue_body=fixture.PACKAGE)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), [{"type": "text", "text": fixture.PACKAGE}])

    def test_invalid_issue_body_stops_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_hook("acme/widget#42", Path(temp), issue_body="Implement feature")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("INVALID: requires exactly one valid status field", result.stderr)
            self.assertEqual(result.stdout, "")

    @unittest.skipUnless(shutil.which("opencode"), "OpenCode CLI not installed")
    def test_opencode_rejects_invalid_github_issue_before_agent_run(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            env = self.issue_environment(directory, "Implement feature")
            env["OPENCODE_CONFIG_DIR"] = str(ROOT / "opencode")
            env["OPENCODE_CONFIG_CONTENT"] = '{"mcp":{"playwright":{"enabled":false}}}'
            env["OPENCODE_DISABLE_MODELS_FETCH"] = "1"
            env["OPENCODE_DISABLE_LSP_DOWNLOAD"] = "1"
            result = subprocess.run(
                ["opencode", "run", "--print-logs", "--log-level", "ERROR", "--command",
                 "implement", "--dir", str(directory), "--format", "json", "acme/widget#42"],
                env=env, cwd=directory, text=True, capture_output=True, check=False, timeout=30,
            )
            self.assertIn("INVALID: requires exactly one valid status field", result.stderr)
            events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
            self.assertFalse(any(event["type"] == "step_start" for event in events))

    def test_invalid_file_stops_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "package.md").write_text("Implement feature")
            result = self.run_hook("package.md", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Invalid Implementation Package", result.stderr)
            self.assertEqual(result.stdout, "")

    def test_missing_source_stops_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for source, expected in (("", "Usage:"), ("missing.md", "Cannot read package file")):
                with self.subTest(source=source):
                    result = self.run_hook(source, directory)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected, result.stderr)
                    self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
