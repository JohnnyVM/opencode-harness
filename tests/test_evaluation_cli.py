import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.evaluate_orchestrator import main


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
        self.assertIn("ready: guadalbot-46", output)

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


if __name__ == "__main__":
    unittest.main()
