import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.evaluate_orchestrator import main
from scripts.orchestrator_eval.case import load_case
from scripts.orchestrator_eval.environment import DoctorReport
from scripts.orchestrator_eval.harness import HarnessResult
from scripts.orchestrator_eval.report import write_report


class EvaluationCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        manifest = root / "evaluation-cases" / "guadalbot-46" / "manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({
            "schema_version": 1,
            "case_id": "guadalbot-46",
            "commands": [{"name": "check", "argv": ["python", "-V"]}],
        }), encoding="utf-8")
        self.root = root

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, argv):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = main(argv)
        return result, output.getvalue(), errors.getvalue()

    def test_help_doctor_and_run(self):
        result, output, _ = self.invoke(["help"])
        self.assertEqual(result, 0)
        self.assertIn("doctor", output)
        result, output, _ = self.invoke(["doctor", "guadalbot-46", "--source-repo", str(self.root)])
        self.assertEqual(result, 0)
        self.assertIn("ok: guadalbot-46", output)
        result, output, _ = self.invoke(["run", "guadalbot-46", "--source-repo", str(self.root)])
        self.assertEqual(result, 0)
        self.assertIn("PASS: guadalbot-46", output)

        result, output, _ = self.invoke(["help", "run"])
        self.assertEqual(result, 0)
        self.assertIn("--discard-raw", output)

    def test_invalid_options_and_cases_return_usage(self):
        for argv in (
            ["--not-an-option"],
            ["doctor", "missing", "--source-repo", str(self.root)],
            ["doctor", "guadalbot-46", "--source", str(self.root)],
        ):
            with self.subTest(argv=argv):
                if len(argv) > 1 and argv[1] == "missing":
                    self.assertEqual(self.invoke(argv)[0], 2)
                else:
                    with self.assertRaises(SystemExit) as raised:
                        main(argv)
                    self.assertEqual(raised.exception.code, 2)

    def test_public_run_coordinates_doctor_and_writes_report(self):
        calls = []
        case = load_case("guadalbot-46", self.root)
        report = DoctorReport(())
        result = HarnessResult("PASS", 0, {"outcome": "PASS"})
        output_root = self.root / "artifacts"
        def fake_run(*args, **kwargs):
            calls.append("run")
            write_report(kwargs["output_root"], result.result)
            return result
        with patch("scripts.orchestrator_eval.cli.doctor_case",
                                side_effect=lambda case_id, source: (calls.append("doctor") or (case, report))), \
             patch("scripts.orchestrator_eval.cli.run_evaluation",
                                side_effect=fake_run):
            status, output, _ = self.invoke(["run", "guadalbot-46", "--source-repo", str(self.root),
                                             "--output-root", str(output_root)])
        self.assertEqual(status, 0)
        self.assertEqual(calls, ["doctor", "run"])
        self.assertIn("PASS: guadalbot-46", output)
        self.assertTrue((output_root / "result.json").exists())

    def test_public_run_propagates_failure_exit(self):
        manifest = self.root / "evaluation-cases" / "guadalbot-46" / "manifest.json"
        manifest.write_text(json.dumps({
            "schema_version": 1, "case_id": "guadalbot-46",
            "commands": [{"name": "fail", "argv": ["python", "-c", "raise SystemExit(7)"]}],
        }), encoding="utf-8")
        result, output, _ = self.invoke(["run", "guadalbot-46", "--source-repo", str(self.root)])
        self.assertEqual(result, 1)
        self.assertIn("FAIL: guadalbot-46", output)


if __name__ == "__main__":
    unittest.main()
