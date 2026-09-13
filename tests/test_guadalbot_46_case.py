import json
from pathlib import Path
import unittest

from scripts.orchestrator_eval.case import load_case


ROOT = Path(__file__).parents[1]
CASE = ROOT / "evaluations" / "implementation-orchestrator" / "guadalbot-46"


class Guadalbot46CaseTests(unittest.TestCase):
    def test_manifest_is_loadable_and_declares_all_assets(self):
        case = load_case("guadalbot-46", ROOT)
        self.assertEqual({Path(asset).name for asset in case.assets}, {
            "package.json", "request.json", "oracle.py", "calibration.py",
            "fake_live_contract.py",
        })
        self.assertEqual(len(case.commands), 2)
        for asset in case.assets:
            self.assertTrue((ROOT / asset).is_file(), asset)

    def test_public_package_has_no_run_specific_secrets(self):
        package = json.loads((CASE / "package.json").read_text(encoding="utf-8"))
        text = json.dumps(package).lower()
        self.assertNotIn("sha", text)
        self.assertNotIn("pull request", text)
        self.assertNotIn("diagnosis", text)


if __name__ == "__main__":
    unittest.main()
