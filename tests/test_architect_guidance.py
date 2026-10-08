"""Tests for Architect guidance and its skill dependencies."""

from pathlib import Path
import unittest


class ArchitectGuidanceTests(unittest.TestCase):
    def test_architect_is_primary_with_required_skills_and_v2_report_guidance(self):
        content = Path("opencode/agents/architect.md").read_text()
        frontmatter = content.split("---", 2)[1]
        self.assertIn("mode: primary", frontmatter)
        self.assertIn("model: openai/gpt-6-luna", frontmatter)
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
        self.assertTrue(all(text in content for text in ("Architecture Package v2", "## Completion response")))

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
        self.assertTrue(all(text in content for text in ("`Implementation Plan`", "Requirements Traceability")))
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
        self.assertIn(
            "IMPLEMENTING -> TESTING -> REVIEWING -> DONE",
            content,
        )
        self.assertNotIn("cleaner", content.lower())
        self.assertNotIn("CLEANING", content)
        self.assertIn("# Tester gate\n\nAfter all initial tickets are complete:", content)
        self.assertIn("returns to the complete Tester gate", content)
        self.assertIn("`HEAD` returns the run to the Tester gate", content)


if __name__ == "__main__":
    unittest.main()
