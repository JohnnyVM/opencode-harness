import json
import tempfile
import unittest
from pathlib import Path

from scripts.orchestrator_eval.trace import aggregate_trace, discover_sessions


class TraceTests(unittest.TestCase):
    def test_recursive_aggregation_and_incomplete_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "root" / "child"
            nested.mkdir(parents=True)
            (nested / "session.jsonl").write_text(json.dumps({
                "version": "0.0.7", "model": "actual/model",
                "usage": {"input": 2, "output": 3},
                "start": 1, "end": 3,
            }) + "\n", encoding="utf-8")
            report = aggregate_trace(root)
            self.assertEqual(len(discover_sessions(root)), 1)
            self.assertEqual(report.model, "actual/model")
            self.assertEqual(report.total_tokens, 5)
            self.assertTrue(report.complete)

    def test_missing_model_is_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.jsonl"
            path.write_text(json.dumps({"usage": {"input": 1}, "start": 1,
                                        "end": 2}) + "\n", encoding="utf-8")
            report = aggregate_trace(directory)
            self.assertFalse(report.complete)
            self.assertIn("model", report.missing)

    def test_nested_usage_wins_over_top_level_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.jsonl"
            path.write_text(json.dumps({"model": "m", "usage": {"input": 2, "output": 3},
                                        "inputTokens": 200, "outputTokens": 300,
                                        "start": 1, "end": 2}) + "\n", encoding="utf-8")
            report = aggregate_trace(directory)
            self.assertEqual(report.total_tokens, 5)

    def test_distinct_models_and_malformed_tokens_are_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.jsonl"
            path.write_text("\n".join(json.dumps(item) for item in (
                {"model": "one", "usage": {"input": 1, "output": 1}, "start": 1, "end": 2},
                {"model": "two", "usage": {"input": "bad", "output": 1}, "start": 2, "end": 3},
            )) + "\n", encoding="utf-8")
            report = aggregate_trace(directory)
            self.assertFalse(report.complete)
            self.assertIn("model-conflict", report.missing)
            self.assertIn("malformed-tokens", report.missing)


if __name__ == "__main__":
    unittest.main()
