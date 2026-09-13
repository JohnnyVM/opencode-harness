import subprocess
import unittest

from scripts.orchestrator_eval.opencode_runner import (
    final_message_is_done, has_single_root, parse_jsonl, parse_tester_report,
    run_opencode,
)


class OpenCodeRunnerTests(unittest.TestCase):
    def test_stdin_command_is_exact_and_jsonl_is_strict(self):
        seen = {}

        def fake(argv, **kwargs):
            seen.update(argv=argv, kwargs=kwargs)
            return subprocess.CompletedProcess(argv, 0,
                stdout='{"sessionID":"root"}\n{"text":"DONE"}\n', stderr="")

        result = run_opencode("implement", runner=fake)
        self.assertEqual(seen["argv"], ["opencode", "run", "--format", "json"])
        self.assertEqual(seen["kwargs"]["input"], "implement")
        self.assertTrue(has_single_root(result.events))
        self.assertTrue(final_message_is_done(result.events))

    def test_tester_requires_latest_structural_pass_and_commit(self):
        commit = "a" * 40
        events = [
            {"agent": "tester", "text": "PASS\nfinal commit: " + commit},
            {"agent": "tester", "text": "incomplete"},
        ]
        self.assertFalse(parse_tester_report(events))
        self.assertTrue(parse_tester_report(events[:1]))

    def test_invalid_jsonl_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_jsonl("not json")


if __name__ == "__main__":
    unittest.main()
