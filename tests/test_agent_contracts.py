import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "opencode" / "agents"
STATE_MACHINE = ROOT / "docs" / "agents" / "orchestrator-state-machine.md"
WORKFLOW = ROOT / "docs" / "agents" / "agent-workflow.md"
IMPLEMENT_COMMAND = ROOT / "opencode" / "commands" / "implement.md"
SETUP_COMMAND = ROOT / "opencode" / "commands" / "setup-matt-pocock-skills.md"
TO_SPEC = ROOT / "opencode" / "skills" / "to-spec" / "SKILL.md"


def read(path):
    return path.read_text()


def compact(text):
    return " ".join(text.split())


def frontmatter(path):
    _, metadata, _ = read(path).split("---", 2)
    return metadata


class AgentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orchestrator = read(AGENTS / "implementation-orchestrator.md")
        cls.orchestrator_compact = compact(cls.orchestrator)
        cls.tester = read(AGENTS / "tester.md")
        cls.reviewer = read(AGENTS / "code-reviewer.md")
        cls.cleaner = read(AGENTS / "cleaner.md")
        cls.spec_design = read(AGENTS / "spec-design.md")
        cls.implement_command = read(IMPLEMENT_COMMAND)
        cls.state_machine = read(STATE_MACHINE)
        cls.workflow = read(WORKFLOW)

    def test_main_path_and_state_vocabulary_are_exact(self):
        states = re.findall(r"^\d+\. `([A-Z_]+)`:", self.state_machine, re.MULTILINE)
        self.assertEqual(
            states,
            [
                "PACKAGE_REFERENCE_RECEIVED",
                "PACKAGE_RESOLVING",
                "SPEC_RECEIVED",
                "PLANNING",
                "IMPLEMENTING",
                "TESTING",
                "DEBUGGING",
                "REVIEWING",
                "BLOCKED_SPEC",
                "BLOCKED_IMPLEMENTATION",
                "BLOCKED_OPERATION",
                "BLOCKED_DIAGNOSIS",
                "DONE",
            ],
        )
        main_path = "SPEC_RECEIVED -> PLANNING -> IMPLEMENTING -> TESTING -> REVIEWING -> DONE"
        self.assertIn(main_path, compact(self.state_machine))
        self.assertIn(main_path, self.orchestrator_compact)

        forbidden = {
            "FINALIZING",
            "LOCAL_TESTING",
            "REMOTE_TESTING",
            "PUBLISHING",
            "COMMITTING",
            "PRE_REVIEWING",
            "CLEANING",
        }
        contracts = [
            self.state_machine,
            self.workflow,
            *[read(path) for path in AGENTS.glob("*.md")],
        ]
        for state in forbidden:
            self.assertTrue(all(state not in contract for contract in contracts), state)

    def test_implement_command_is_primary_and_forwards_one_reference(self):
        metadata = frontmatter(IMPLEMENT_COMMAND)
        self.assertIn("agent: implementation-orchestrator", metadata)
        self.assertIn("subtask: false", metadata)
        self.assertEqual(self.implement_command.count("$ARGUMENTS"), 1)

    def test_setup_command_forwards_arguments_and_can_write_its_outputs(self):
        command = read(SETUP_COMMAND)
        metadata = frontmatter(SETUP_COMMAND)
        spec_metadata = frontmatter(AGENTS / "spec-design.md")
        setup_skill = read(
            ROOT / "opencode" / "skills" / "setup-matt-pocock-skills" / "SKILL.md"
        )

        self.assertIn("agent: spec-design", metadata)
        self.assertEqual(command.count("$ARGUMENTS"), 1)
        self.assertIn('"AGENTS.md": allow', spec_metadata)
        self.assertNotIn(".scratch", spec_metadata)
        self.assertIn("`--tracker github`", setup_skill)
        self.assertIn("`--tracker local`", setup_skill)
        self.assertNotIn("--tracker markdown", setup_skill)
        local_seed = read(
            ROOT
            / "opencode"
            / "skills"
            / "setup-matt-pocock-skills"
            / "issue-tracker-local.md"
        )
        self.assertIn("`docs/issues/<issue-id>.md`", local_seed)
        self.assertIn("state: open", local_seed)
        self.assertIn("reject absolute paths", local_seed)
        self.assertFalse((AGENTS / "bug-finder.md").exists())

    def test_issue_reference_protocol_values_are_documented(self):
        for reference in ("`#<number>`", "`<owner>/<repository>#<number>`"):
            self.assertIn(reference, self.orchestrator)
            self.assertIn(reference, self.state_machine)
        self.assertIn(
            "gh issue view <number> --repo <owner>/<repository>",
            self.state_machine,
        )
        self.assertIn("gh issue view <url>", self.state_machine)

    def test_package_intake_state_path_is_documented(self):
        intake = (
            "PACKAGE_REFERENCE_RECEIVED -> PACKAGE_RESOLVING -> SPEC_RECEIVED -> PLANNING"
        )
        self.assertIn(intake, self.orchestrator_compact)

    def test_approval_field_is_not_persisted(self):
        contracts = (
            self.orchestrator,
            self.spec_design,
            read(ROOT / "docs" / "issue-tracker.md"),
            read(
                ROOT
                / "opencode"
                / "skills"
                / "setup-matt-pocock-skills"
                / "issue-tracker-github.md"
            ),
        )
        for contract in contracts:
            self.assertNotIn("approved_by_user", contract)

    def test_only_issue_view_intake_is_allowed_without_prompting(self):
        metadata = frontmatter(AGENTS / "implementation-orchestrator.md")
        broad = metadata.index('"gh *": ask')
        issue_view = metadata.index('"gh issue view*": allow')
        self.assertLess(broad, issue_view)
        gh_allows = re.findall(r'^\s+"(gh [^"]+)": allow$', metadata, re.MULTILINE)
        self.assertEqual(gh_allows, ["gh issue view*"])

    def test_package_producer_and_consumer_share_execution_identity(self):
        contracts = (
            read(TO_SPEC),
            self.spec_design,
            self.orchestrator,
            self.state_machine,
            read(ROOT / "docs" / "issue-tracker.md"),
            read(ROOT / "CONTEXT.md"),
        )
        for contract in contracts:
            self.assertIn("target_repository", contract)
            self.assertIn("implementation_branch", contract)

        self.assertNotIn("comments,url", self.orchestrator)

    def test_reviewer_operation_blocker_protocol(self):
        self.assertIn("BLOCKED: HEAD_MISMATCH", self.reviewer)
        self.assertIn("REVIEWING -- HEAD_MISMATCH --> BLOCKED_OPERATION", self.state_machine)

    def test_default_agent(self):
        config = json.loads(read(ROOT / "opencode" / "opencode.jsonc"))
        self.assertEqual(config["default_agent"], "spec-design")

    def test_debugger_permissions(self):
        self.assertIn(
            '"debugger": allow',
            frontmatter(AGENTS / "implementation-orchestrator.md"),
        )
        self.assertIn('"*": deny', frontmatter(AGENTS / "tester.md"))

    def test_tester_has_binary_result_and_exactly_three_routing_reasons(self):
        statuses = re.findall(r"^- `status: ([A-Z_]+)`:", self.tester, re.MULTILINE)
        reasons = re.findall(r"^- `reason: ([A-Z_]+)`:", self.tester, re.MULTILINE)
        self.assertEqual(statuses, ["PASS", "NOT_PASS"])
        self.assertEqual(reasons, ["CHECK_FAILURE", "INFRASTRUCTURE", "CONFIGURATION"])
        self.assertIn("status: PASS | NOT_PASS", self.tester)
        for obsolete in ("status: FAIL", "INFRA_BLOCKED", "CONFIG_MISSING"):
            self.assertNotIn(obsolete, self.tester)

    def test_reviewer_testing_blocker_protocol(self):
        self.assertIn("BLOCKED: TESTING_NOT_PASSED", self.reviewer)

    def test_reviewer_head_evidence_command(self):
        self.assertIn("git rev-parse HEAD", self.reviewer)

    def test_cleaner_is_leaf_read_only_and_only_orchestrator_can_invoke_it(self):
        metadata = frontmatter(AGENTS / "cleaner.md")
        self.assertIn("model: openai/gpt-5.6-sol", metadata)
        for permission in (
            "edit: deny",
            "question: deny",
            "skill: deny",
            "external_directory: deny",
        ):
            self.assertIn(permission, metadata)
        self.assertIn('task:\n    "*": deny', metadata)
        bash_rules = [
            line.strip()
            for line in metadata.split("  bash:\n", 1)[1].splitlines()
            if line.strip()
        ]
        self.assertEqual(
            bash_rules,
            ['"*": deny', '"git rev-parse HEAD": allow'],
        )

        invokers = []
        for path in AGENTS.glob("*.md"):
            if '"cleaner": allow' in frontmatter(path):
                invokers.append(path.name)
        self.assertEqual(invokers, ["implementation-orchestrator.md"])

        config = json.loads(read(ROOT / "opencode" / "opencode.jsonc"))
        self.assertEqual(config["subagent_depth"], 1)

    def test_cleaner_has_binary_result(self):
        statuses = set(re.findall(r"status: ([A-Z_]+)", self.cleaner))
        self.assertEqual(statuses, {"PASS", "NOT_PASS"})
        self.assertIn("status: PASS", self.cleaner)
        self.assertIn("status: NOT_PASS", self.cleaner)

    def test_cleaner_precondition_failure_protocol(self):
        self.assertIn(
            "precondition failure: MISSING_INPUT | CONTRADICTORY_INPUT | HEAD_MISMATCH",
            self.cleaner,
        )

    def test_orchestrator_disallows_destructive_integration_commands(self):
        metadata = frontmatter(AGENTS / "implementation-orchestrator.md")
        self.assertNotIn('"git merge --ff-only *": allow', metadata)
        for destructive in ("git reset", "git clean", "git rebase"):
            self.assertNotIn(f'"{destructive}*": allow', metadata)


if __name__ == "__main__":
    unittest.main()
