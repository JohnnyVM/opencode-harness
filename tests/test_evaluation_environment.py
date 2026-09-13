import unittest
from unittest.mock import patch

from scripts.orchestrator_eval.environment import check_prerequisites


class EnvironmentTests(unittest.TestCase):
    def test_doctor_is_exhaustive_and_skips_dependent_queries(self):
        with patch("scripts.orchestrator_eval.environment.platform.system", return_value="Linux"), \
             patch("scripts.orchestrator_eval.environment.platform.machine", return_value="x86_64"), \
             patch("scripts.orchestrator_eval.environment.shutil.which", return_value=None):
            report = check_prerequisites(required_tools=("git", "docker"), versions={"git": "2"}, image="eval:latest")
        self.assertEqual([check.status for check in report.checks], ["passed", "passed", "failed", "failed", "skipped", "skipped"])
        self.assertFalse(report.ok)


if __name__ == "__main__":
    unittest.main()
