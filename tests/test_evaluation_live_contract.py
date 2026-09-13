import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).parents[1]
CASE = ROOT / "evaluations" / "implementation-orchestrator" / "guadalbot-46"


class EvaluationLiveContractTests(unittest.TestCase):
    def test_contract_is_fake_only_and_precondition_gated(self):
        script = CASE / "fake_live_contract.py"
        result = subprocess.run([sys.executable, str(script)], capture_output=True,
                                text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["outcome"], "SKIP")

    def test_explicit_live_flag_does_not_start_a_service(self):
        script = CASE / "fake_live_contract.py"
        env = {"GUADALBOT46_LIVE": "1", "PATH": "/usr/bin:/bin"}
        result = subprocess.run([sys.executable, str(script)], env=env,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("external runner", result.stderr)


if __name__ == "__main__":
    unittest.main()
