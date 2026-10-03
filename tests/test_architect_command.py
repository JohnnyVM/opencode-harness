import json
from pathlib import Path
import tempfile
import unittest

from tests.test_implement_command import run_hook

ROOT = Path(__file__).resolve().parents[1]
SPECIFICATION = """status: SPEC_APPROVED_BY_AGENT
## Problem Statement
Problem
## Solution
Solution
## User Stories
Story
## Product Decisions and Constraints
Decision
## Testing Decisions
Test
## Acceptance Criteria
- AC1: Observable result
## Risks
None
## Explicit Unknowns
None
## Out of Scope
None
"""
def invoke(source, output, directory, issue=None):
    return run_hook(
        f"{source} --output {output}", directory, issue=issue, command="architect"
    )


class ArchitectCommandTests(unittest.TestCase):
    def test_local_source_exact_text_normalized_path_and_spaces(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = "spec with spaces.md"
            output = "folder with spaces/architecture package.md"
            (directory / source).write_text(SPECIFICATION)
            result = invoke(source, output, directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            parts = json.loads(result.stdout)
            self.assertEqual(
                parts[0]["text"],
                f"Create an Architecture Package and write it to this output path: {(directory / output).resolve()}",
            )
            self.assertEqual(parts[1], {"type": "text", "text": SPECIFICATION})

            quoted = run_hook(
                f'"{source} --output {output}"', directory, command="architect"
            )
            self.assertEqual(quoted.returncode, 0, quoted.stderr)
            self.assertEqual(json.loads(quoted.stdout)[1]["text"], SPECIFICATION)

    def test_issue_open_closed_url_and_malformed(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for state, expected in (("OPEN", 2), ("CLOSED", 3)):
                result = invoke("acme/widget#42", "out.md", directory,
                                issue={"body": SPECIFICATION, "state": state})
                self.assertEqual(result.returncode, 0, result.stderr)
                parts = json.loads(result.stdout)
                self.assertEqual(len(parts), expected)
                self.assertEqual(parts[1]["text"], SPECIFICATION)
                if state == "CLOSED": self.assertIn("CLOSED_ISSUE_CLARIFICATION_REQUIRED", parts[2]["text"])
            result = invoke("https://github.com/acme/widget/issues/42", "out.md", directory,
                            issue={"body": "not a specification"})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Invalid Specification Package", result.stderr)
            self.assertEqual(result.stdout, "")


class ArchitectArgumentTests(unittest.TestCase):
    def test_output_forms_are_equivalent(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "brand-selection.md").write_text(SPECIFICATION)
            results = [run_hook(args, directory, command="architect") for args in (
                "brand-selection.md brand-selection-architecture.md",
                "brand-selection.md --output brand-selection-architecture.md",
                "brand-selection.md",
            )]
            for result in results:
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(results[0].stdout, results[1].stdout)
            self.assertEqual(results[1].stdout, results[2].stdout)
            self.assertIn(str(directory / "brand-selection-architecture.md"), results[0].stdout)

    def test_quoted_positional_paths_and_default_without_extension(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "spec with spaces.md").write_text(SPECIFICATION)
            (directory / "spec").write_text(SPECIFICATION)
            for args, output in (
                ('"spec with spaces.md" "folder with spaces/out.md"', "folder with spaces/out.md"),
                ('"spec with spaces.md" --output "folder with spaces/out.md"', "folder with spaces/out.md"),
                ('"spec with spaces.md"', "spec with spaces-architecture.md"),
                ("spec", "spec-architecture"),
            ):
                with self.subTest(args=args):
                    result = run_hook(args, directory, command="architect")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    parts = json.loads(result.stdout)
                    self.assertIn(str(directory / output), parts[0]["text"])
                    self.assertEqual(parts[1]["text"], SPECIFICATION)

    def test_requires_unambiguous_arguments_and_source(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for args in ("", "missing.md", "missing.md --output ", "a --output b --output c",
                         "a b c", '"unclosed', "--output out.md", 'a ""'):
                result = run_hook(args, directory, command="architect")
                self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
