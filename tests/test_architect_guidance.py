"""Tests for the model-neutral Architect and its skill dependencies."""

from pathlib import Path
import unittest


class ArchitectGuidanceTests(unittest.TestCase):
    def test_architect_is_model_neutral_primary_with_required_skills(self):
        content = Path("opencode/agents/architect.md").read_text()
        frontmatter = content.split("---", 2)[1]
        self.assertIn("mode: primary", frontmatter)
        self.assertNotIn("\nmodel:", frontmatter)
        for name in ("architect", "how", "arena", "why", "interrogate"):
            self.assertIn(f'"{name}": allow', frontmatter)
        self.assertIn("do not implement production code", content.lower())
        self.assertIn("`runs-on` labels", content)
        for command in (
            '"git branch --show-current": allow',
            '"git add *": allow',
            '"git commit -m *": allow',
            '"git rev-parse HEAD": allow',
        ):
            with self.subTest(command=command):
                self.assertIn(command, frontmatter)
        self.assertIn("On any branch other than `main`", content)
        self.assertIn("stage only the generated Architecture Package", content)
        self.assertIn("Do not stage unrelated changes", content)
        self.assertIn("Verify the worktree is clean after the commit", content)
        self.assertIn("complete\n   40-character `git rev-parse HEAD` output", content)
        self.assertIn("GitHub issue source has no local", content)
        self.assertIn("make remote\n   writes", content)

    def test_dependency_skills_and_references_exist(self):
        skills = Path("opencode/skills")
        for name in ("architect", "how", "arena", "why", "interrogate"):
            with self.subTest(skill=name):
                entrypoint = skills / name / "SKILL.md"
                self.assertTrue(entrypoint.is_file())
                self.assertIn(f"name: {name}", entrypoint.read_text())
        for name in ("runner-prompt.md", "rationale-template.md", "design-red-flags.md"):
            self.assertTrue((skills / "architect" / name).is_file())

    def test_implementation_orchestrator_embeds_coder_assignment_shape(self):
        content = Path("opencode/agents/implementation-orchestrator.md").read_text()
        for field in (
            "- Ticket:", "- Dependencies:", "- Allowed:", "- Forbidden:", "- Approach:",
            "- AC1: verbatim criterion",
            "### C1", "- Command:", "- Working directory:", "- Prerequisites:",
            "- Expected:", "- Branch:", "- Baseline:", "- Expected HEAD:",
            "- Expected candidate:", "- Additional allowed scope:",
        ):
            with self.subTest(field=field):
                self.assertIn(field, content)
        self.assertIn("complete 40-character output", content)
        self.assertIn("paste it verbatim into each review packet", content)
        self.assertIn("exit-zero skipped workflow", content)
        cleaner = Path("opencode/agents/cleaner.md").read_text()
        self.assertIn(
            "IMPLEMENTING -> CLEANING -> TESTING -> REVIEWING -> DONE",
            content,
        )
        self.assertLess(content.index("# Cleaner gate"), content.index("# Tester gate"))
        self.assertIn("exact `git diff` for the current uncommitted", content)
        self.assertIn("do not substitute a baseline-to-`HEAD` diff", content)
        self.assertIn("before final verification and Code Review", cleaner)
        self.assertNotIn("every applicable Tester `PASS` report", cleaner)
        self.assertNotIn("Code Reviewer approval", cleaner)


if __name__ == "__main__":
    unittest.main()
