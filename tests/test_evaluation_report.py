import json
from pathlib import Path
import tempfile
import unittest

from scripts.orchestrator_eval.report import write_report


class EvaluationReportTests(unittest.TestCase):
    def test_json_is_authoritative_and_artifacts_are_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "artifacts"
            json_path, markdown_path = write_report(directory, {
                "outcome": "PASS", "case_id": "fixture", "model": "actual",
                "results": [{"name": "oracle", "outcome": "PASS"}],
            }, raw='{"private":true}\n')
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("# Evaluation: PASS", markdown)
            self.assertIn('"outcome": "PASS"', markdown)
            self.assertIn("- **model:** actual", markdown)
            self.assertEqual(json_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(markdown_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual((directory / "raw.jsonl").stat().st_mode & 0o777, 0o600)
            self.assertEqual(payload["model"], "actual")
            self.assertEqual(list(directory.glob(".*")), [])


if __name__ == "__main__":
    unittest.main()
