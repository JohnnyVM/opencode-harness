import os
from pathlib import Path
import subprocess
import unittest

from scripts.orchestrator_eval.oracle import (
    OracleProtocolError,
    OracleResult,
    oracle_environment,
    reduce_results,
    run_oracle,
)


class OracleTests(unittest.TestCase):
    def test_invocation_uses_frozen_root_and_removes_credentials(self):
        seen = {}

        def fake(argv, **kwargs):
            seen.update(argv=argv, kwargs=kwargs)
            return subprocess.CompletedProcess(argv, 0, '{"outcome":"PASS","model":"actual"}', "")

        old = os.environ.get("EVALUATION_API_TOKEN")
        os.environ["EVALUATION_API_TOKEN"] = "must-not-leak"
        try:
            result = run_oracle(("oracle",), {"case": "x"},
                                verification_root=Path("/frozen"), runner=fake)
        finally:
            if old is None:
                os.environ.pop("EVALUATION_API_TOKEN", None)
            else:
                os.environ["EVALUATION_API_TOKEN"] = old
        self.assertEqual(result.model, "actual")
        self.assertEqual(seen["kwargs"]["cwd"], Path("/frozen"))
        self.assertNotIn("EVALUATION_API_TOKEN", seen["kwargs"]["env"])
        self.assertEqual(seen["kwargs"]["env"]["OPENCODE_EVALUATION_FROZEN"], "1")

    def test_protocol_fault_is_not_an_evaluation_failure(self):
        def fake(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, "not-json", "")

        with self.assertRaises(OracleProtocolError):
            run_oracle(("oracle",), {}, verification_root=Path("/frozen"), runner=fake)

    def test_reduction_requires_every_oracle_to_pass(self):
        passed = OracleResult("PASS", {})
        failed = OracleResult("FAIL", {})
        self.assertEqual(reduce_results([passed, passed]), "PASS")
        self.assertEqual(reduce_results([passed, failed]), "FAIL")
        self.assertEqual(reduce_results([]), "SKIP")


if __name__ == "__main__":
    unittest.main()
