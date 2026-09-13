import json
from pathlib import Path
import tempfile
import unittest

from scripts.orchestrator_eval.case import CaseError, ExitCode, Status, load_case


class EvaluationCaseTests(unittest.TestCase):
    def write_manifest(self, root, value):
        manifest = Path(root) / "evaluation-cases" / "guadalbot-46" / "manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps(value), encoding="utf-8")

    def valid_manifest(self):
        return {
            "schema_version": 1,
            "case_id": "guadalbot-46",
            "description": "smoke",
            "commands": [{"name": "check", "argv": ["python", "-V"]}],
        }

    def test_loads_versioned_case_and_defaults_expectations(self):
        with tempfile.TemporaryDirectory() as root:
            self.write_manifest(root, self.valid_manifest())
            case = load_case("guadalbot-46", root)
        self.assertEqual(case.schema_version, 1)
        self.assertEqual(case.commands[0].expected_status, Status.PASSED)
        self.assertEqual(case.commands[0].expected_exit_code, ExitCode.SUCCESS)

    def test_rejects_unknown_keys_and_invalid_values(self):
        cases = [
            {**self.valid_manifest(), "extra": True},
            {**self.valid_manifest(), "schema_version": True},
            {**self.valid_manifest(), "commands": [{"name": "x", "argv": ["x"], "cwd": "../outside"}]},
            {**self.valid_manifest(), "commands": [{"name": "x", "argv": [""]}]},
            {**self.valid_manifest(), "commands": [{"name": "x", "argv": ["x"], "expected_exit_code": 256}]},
        ]
        for value in cases:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as root:
                self.write_manifest(root, value)
                with self.assertRaises(CaseError):
                    load_case("guadalbot-46", root)

    def test_rejects_unknown_case_and_missing_repository(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(CaseError):
                load_case("other", root)
        with self.assertRaises(CaseError):
            load_case("guadalbot-46", "/does/not/exist")


if __name__ == "__main__":
    unittest.main()
