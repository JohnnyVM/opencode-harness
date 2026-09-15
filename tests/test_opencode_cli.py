"""Black-box checks for OpenCode's resolved `/implement` command."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
OPENCODE = os.environ.get("OPENCODE_BIN") or shutil.which("opencode")
ISSUE_REFERENCE = "Guadalsistema/guadalsistema-odoo-modules#109"


@unittest.skipUnless(OPENCODE, "OpenCode CLI is not installed")
class OpenCodeCommandRoutingTests(unittest.TestCase):
    def test_implement_transmits_only_the_issue_reference_to_orchestrator(self):
        assert OPENCODE is not None
        environment = os.environ.copy()
        environment.update(
            {
                "OPENCODE_CONFIG": str(ROOT / "opencode" / "opencode.jsonc"),
                "OPENCODE_CONFIG_DIR": str(ROOT / "opencode"),
                "OPENCODE_CONFIG_CONTENT": '{"mcp":{"playwright":{"enabled":false}}}',
                "OPENCODE_DISABLE_MODELS_FETCH": "1",
                "OPENCODE_DISABLE_LSP_DOWNLOAD": "1",
            }
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "config.json"
            with output.open("w") as stream:
                result = subprocess.run(
                    [OPENCODE, "--pure", "debug", "config"],
                    cwd=ROOT,
                    env=environment,
                    text=True,
                    stdout=stream,
                    stderr=subprocess.PIPE,
                    timeout=30,
                    check=False,
                )
            self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads(output.read_text())

        command = config["command"]["implement"]
        self.assertEqual(command["agent"], "implementation-orchestrator")
        self.assertFalse(command["subtask"])
        self.assertEqual(command["template"], "$ARGUMENTS")
        self.assertEqual(command["template"].replace("$ARGUMENTS", ISSUE_REFERENCE), ISSUE_REFERENCE)


if __name__ == "__main__":
    unittest.main()
