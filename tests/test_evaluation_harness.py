from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.orchestrator_eval.harness import OUTCOME_EXIT, outcome_exit, run_oracles
from scripts.orchestrator_eval.oracle import OracleProtocolError, OracleResult


class EvaluationHarnessTests(unittest.TestCase):
    def test_outcome_exit_precedence_and_protocol_error(self):
        self.assertEqual(outcome_exit("PASS"), 0)
        self.assertEqual(outcome_exit("FAIL"), 1)
        self.assertEqual(outcome_exit("HARNESS_ERROR"), 2)
        self.assertEqual(OUTCOME_EXIT["SKIP"], 0)

        def fake(command, request, **kwargs):
            if command == ("bad",):
                raise OracleProtocolError("malformed response")
            return OracleResult("FAIL", {}, model="actual")

        with tempfile.TemporaryDirectory() as temporary:
            with patch("scripts.orchestrator_eval.harness.run_oracle", side_effect=fake):
                result = run_oracles([("bad",), ("later",)], {},
                                     verification_root=Path(temporary), output_root=Path(temporary) / "out")
            self.assertEqual(result.outcome, "HARNESS_ERROR")
            self.assertEqual(result.exit_code, 2)
            self.assertTrue((Path(temporary) / "out" / "result.json").exists())

    def test_fail_is_reduced_only_after_all_oracles_run(self):
        calls = []

        def fake(command, request, **kwargs):
            calls.append(command)
            return OracleResult("FAIL" if command == ("first",) else "PASS", {}, model="actual")

        with patch("scripts.orchestrator_eval.harness.run_oracle", side_effect=fake):
            result = run_oracles([("first",), ("second",)], {}, verification_root=Path("/frozen"))
        self.assertEqual(result.outcome, "FAIL")
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(calls, [("first",), ("second",)])


if __name__ == "__main__":
    unittest.main()
