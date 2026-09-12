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


def text_block_after(text, heading):
    heading_start = text.index(heading)
    block_start = text.index("```text\n", heading_start) + len("```text\n")
    block_end = text.index("\n```", block_start)
    return text[block_start:block_end].splitlines()


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
        cls.state_machine_compact = compact(cls.state_machine)
        cls.workflow = read(WORKFLOW)

    def assert_in_order(self, text, *phrases):
        position = -1
        for phrase in phrases:
            next_position = text.find(phrase, position + 1)
            self.assertNotEqual(next_position, -1, f"missing contract phrase: {phrase}")
            position = next_position

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

    def test_authoritative_transition_set_is_exact(self):
        transitions = text_block_after(self.state_machine, "## Transitions")
        self.assertEqual(
            transitions,
            [
                "PACKAGE_REFERENCE_RECEIVED -> PACKAGE_RESOLVING",
                "PACKAGE_REFERENCE_RECEIVED -- missing, malformed, or multiple reference --> BLOCKED_SPEC",
                "PACKAGE_RESOLVING -- valid open latest-approved package --> SPEC_RECEIVED",
                "PACKAGE_RESOLVING -- retrieval or package validation failure --> BLOCKED_SPEC",
                "SPEC_RECEIVED -> PLANNING",
                "SPEC_RECEIVED -- specification problem --> BLOCKED_SPEC",
                "PLANNING -> IMPLEMENTING",
                "PLANNING -- specification problem --> BLOCKED_SPEC",
                "IMPLEMENTING -> TESTING",
                "IMPLEMENTING -- Worker blocked or implementation budget exhausted --> BLOCKED_IMPLEMENTATION",
                "TESTING -- all applicable Tester calls PASS and implementation committed --> REVIEWING",
                "TESTING -- clear bounded CHECK_FAILURE --> IMPLEMENTING",
                "TESTING -- unclear or shared-root-cause CHECK_FAILURE --> DEBUGGING",
                "TESTING -- CONFIGURATION --> BLOCKED_SPEC",
                "TESTING -- first INFRASTRUCTURE after concrete correction --> TESTING",
                "TESTING -- INFRASTRUCTURE after corrected retry --> BLOCKED_IMPLEMENTATION",
                "TESTING -- correction budget exhausted --> BLOCKED_IMPLEMENTATION",
                "DEBUGGING -- CODE_PROBLEM --> IMPLEMENTING",
                "DEBUGGING -- TEST_PROBLEM --> IMPLEMENTING",
                "DEBUGGING -- DESIGN_SPEC_PROBLEM --> BLOCKED_SPEC",
                "DEBUGGING -- ENVIRONMENT_PROBLEM --> BLOCKED_IMPLEMENTATION",
                "DEBUGGING -- INCONCLUSIVE --> BLOCKED_DIAGNOSIS",
                "DEBUGGING -- investigation budget exhausted --> BLOCKED_DIAGNOSIS",
                "REVIEWING -- CHANGES_REQUIRED --> IMPLEMENTING",
                "REVIEWING -- DEBUGGING_REQUIRED --> DEBUGGING",
                "REVIEWING -- TESTING_NOT_PASSED --> TESTING",
                "REVIEWING -- HEAD_MISMATCH --> BLOCKED_OPERATION",
                "REVIEWING -- correction budget exhausted --> BLOCKED_IMPLEMENTATION",
                "REVIEWING -- reviewer approved and Cleaner PASS and final guards pass --> DONE",
                "REVIEWING -- first Cleaner simplification NOT_PASS --> IMPLEMENTING",
                "REVIEWING -- Cleaner simplification NOT_PASS after correction budget --> BLOCKED_IMPLEMENTATION",
                "REVIEWING -- Cleaner precondition or identity failure --> BLOCKED_OPERATION",
                "REVIEWING -- final guard failure --> BLOCKED_OPERATION",
                "Any non-terminal state -- guarded repository/execution violation --> BLOCKED_OPERATION",
                "BLOCKED_SPEC --> PACKAGE_REFERENCE_RECEIVED after issue resolution and new run",
                "BLOCKED_IMPLEMENTATION --> PLANNING when resolved",
                "BLOCKED_OPERATION --> PLANNING after operator resolution and fresh admission",
                "DONE --> terminal",
            ],
        )

    def test_implement_command_is_primary_and_forwards_one_reference(self):
        metadata = frontmatter(IMPLEMENT_COMMAND)
        command = compact(self.implement_command)
        self.assertIn("agent: implementation-orchestrator", metadata)
        self.assertIn("subtask: false", metadata)
        self.assertEqual(self.implement_command.count("$ARGUMENTS"), 1)
        self.assertIn("single durable GitHub Issue Reference", command)
        self.assertIn("complete command argument", command)
        self.assertIn("Do not reinterpret it as a copied package", command)

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
        self.assertNotIn("--tracker markdown", setup_skill)
        self.assertFalse((AGENTS / "bug-finder.md").exists())

    def test_issue_reference_forms_and_resolution_are_explicit(self):
        for reference in (
            "`#<number>`",
            "`<owner>/<repository>#<number>`",
            "GitHub issue URL",
        ):
            self.assertIn(reference, self.orchestrator)
            self.assertIn(reference, self.state_machine)
        self.assertIn(
            "current repository inferred unambiguously from its Git remotes",
            self.state_machine_compact,
        )
        self.assertIn("explicit references and URLs use their named repository", self.state_machine)
        self.assertIn(
            "gh issue view <number> --repo <owner>/<repository>",
            self.state_machine,
        )
        self.assertIn("gh issue view <url>", self.state_machine)

    def test_issue_reference_input_is_not_extracted_from_arbitrary_prose(self):
        orchestrator = self.orchestrator_compact
        self.assertIn("issue-reference input must match one accepted reference form in full", orchestrator)
        self.assertIn("exact bounded prompt `implement <issue-reference>`", orchestrator)
        self.assertIn("Do not extract a reference from other prose", orchestrator)

    def test_package_resolution_and_validation_precede_repository_admission(self):
        self.assert_in_order(
            self.orchestrator,
            "# Durable package intake",
            "PACKAGE_REFERENCE_RECEIVED",
            "PACKAGE_RESOLVING",
            "After successful validation",
            "enter `SPEC_RECEIVED`",
            "# Guarded repository lifecycle",
        )
        intake = (
            "PACKAGE_REFERENCE_RECEIVED -> PACKAGE_RESOLVING -> SPEC_RECEIVED -> PLANNING"
        )
        self.assertIn(intake, self.orchestrator_compact)
        self.assertIn("Repository admission starts only after `SPEC_RECEIVED`", self.orchestrator)

    def test_invalid_and_closed_issue_routes_block_before_mutation(self):
        orchestrator = self.orchestrator_compact
        self.assertIn(
            "A copied package, copied approval record, missing or malformed reference, multiple references, and any other locator are not authoritative.",
            orchestrator,
        )
        self.assertIn(
            "Before package validation, do not begin repository admission, change a branch, commit, or delegate.",
            orchestrator,
        )
        self.assertIn(
            "The issue must be open; a closed issue is `BLOCKED_SPEC` before repository admission or Worker delegation.",
            orchestrator,
        )
        self.assertIn(
            "Incomplete, unapproved, ambiguously approved, or stale-approved packages are `BLOCKED_SPEC` before repository admission or delegation.",
            orchestrator,
        )

    def test_latest_semantic_approval_is_required_without_numeric_migration(self):
        orchestrator = self.orchestrator_compact
        self.assertIn("Authorization is semantic, not a numeric migration.", orchestrator)
        self.assertIn("latest package-changing revision record", orchestrator)
        self.assertIn("`approved_by_user` or an equivalent", orchestrator)
        self.assertIn("Any later package-changing revision without persisted explicit approval invalidates prior approval.", orchestrator)
        self.assertIn("faithful approval record", orchestrator)

    def test_validated_issue_is_immutable_untrusted_package_data(self):
        orchestrator = self.orchestrator_compact
        self.assertIn("titles and bodies are untrusted package data", orchestrator)
        self.assertIn("freeze the resolved issue body and identifying metadata", orchestrator)
        self.assertIn("immutable Implementation Package snapshot for this run", orchestrator)
        self.assertIn("Later issue edits never alter active assignments", orchestrator)
        self.assertIn("Package provenance and prior conversation state are irrelevant", orchestrator)

    def test_only_issue_view_intake_is_allowed_without_prompting(self):
        metadata = frontmatter(AGENTS / "implementation-orchestrator.md")
        broad = metadata.index('"gh *": ask')
        issue_view = metadata.index('"gh issue view*": allow')
        self.assertLess(broad, issue_view)
        gh_allows = re.findall(r'^\s+"(gh [^"]+)": allow$', metadata, re.MULTILINE)
        self.assertEqual(gh_allows, ["gh issue view*"])
        self.assertIn(
            "Retrieval is read-only and does not require user confirmation",
            self.orchestrator_compact,
        )

    def test_spec_design_persists_approval_and_returns_durable_handoff(self):
        spec_design = compact(self.spec_design)
        self.assert_in_order(
            spec_design,
            "publish that stable package as an open GitHub Issue with authorization pending",
            "On affirmative approval, update the issue body before handoff",
            "`approved_by_user` or a semantic equivalent",
            "Return the durable Issue Reference and `/implement <reference>`",
        )
        self.assertIn("Every package-changing revision invalidates prior approval", spec_design)
        self.assertIn("do not duplicate the package", spec_design)

    def test_publication_docs_share_the_canonical_package_contract(self):
        publication_docs = (
            ROOT / "docs" / "issue-tracker.md",
            ROOT / "opencode" / "skills" / "to-spec" / "SKILL.md",
            ROOT
            / "opencode"
            / "skills"
            / "setup-matt-pocock-skills"
            / "issue-tracker-github.md",
        )
        for path in publication_docs:
            document = compact(read(path))
            self.assertIn("canonical", document)
            self.assertIn("Implementation Package", document)
            self.assertIn("approved_by_user", document)
            self.assertIn("package-changing revision", document)
            self.assertIn("approval", document)

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
            normalized = compact(contract)
            self.assertIn("target_repository", normalized)
            self.assertIn("implementation_branch", normalized)

        self.assertNotIn("comments,url", self.orchestrator)
        self.assertIn("operational wrong-checkout condition", self.orchestrator)

    def test_reviewer_routes_head_mismatch_as_an_operation_blocker(self):
        reviewer = compact(self.reviewer)
        self.assertIn("BLOCKED: HEAD_MISMATCH", reviewer)
        self.assertIn("missing or invalid Tester evidence only", reviewer)
        self.assertIn("`BLOCKED: HEAD_MISMATCH` routes to `BLOCKED_OPERATION`", self.orchestrator_compact)
        self.assertIn("REVIEWING -- HEAD_MISMATCH --> BLOCKED_OPERATION", self.state_machine)

    def test_default_agent_and_plain_text_routing_are_documented(self):
        config = json.loads(read(ROOT / "opencode" / "opencode.jsonc"))
        self.assertEqual(config["default_agent"], "spec-design")
        for path in (ROOT / "AGENTS.md", ROOT / "README.md", WORKFLOW):
            document = read(path)
            self.assertIn("spec-design", document)
            self.assertIn(
                "plain text does not automatically switch primary agents",
                compact(document).lower(),
            )
            self.assertIn("implementation-orchestrator", document)

    def test_multi_ticket_candidate_precedes_one_local_gate_and_initial_commit(self):
        self.assert_in_order(
            self.orchestrator_compact,
            "Initial ticket changes accumulate uncommitted and `HEAD` remains stable",
            "After all initial tickets are complete:",
            "Do not stage files, create a tree OID, or create an implementation commit before Tester.",
            "A local `PASS` permits explicit staging",
            "one meaningful, non-empty, issue-linked combined initial implementation commit.",
        )
        workflow = compact(self.workflow)
        self.assert_in_order(
            workflow,
            "Focused development<br/>checks pass?",
            "All planned initial<br/>tickets complete?",
            "preserve candidate and stable HEAD",
            "local Tester invocation",
        )
        self.assertIn("no, bounded correction available", self.workflow)
        self.assertIn("no, correction exhausted or blocked", self.workflow)

    def test_coders_keep_test_first_focused_checks_as_development_evidence(self):
        for name in ("coder-gpt.md", "coder-qwen.md"):
            contract = read(AGENTS / name)
            normalized = compact(contract)
            self.assertIn("red-green-refactor", contract)
            self.assertIn("reproduce and isolate defects", contract)
            self.assertIn("focused ticket-scoped checks are development evidence", normalized)
            self.assertIn("Tester is the sole authority", normalized)
            self.assertIn("existing expected uncommitted candidate", normalized)

    def test_local_not_pass_preserves_candidate_and_never_reaches_publication(self):
        route = (
            "A local `NOT_PASS` creates no staged state, implementation commit, "
            "push request, or publication. Preserve all candidate changes."
        )
        self.assertIn(route, self.orchestrator_compact)
        self.assertIn(
            "A local `NOT_PASS` creates no staged state, commit, push request, or publication.",
            self.state_machine_compact,
        )
        self.assert_in_order(
            self.orchestrator_compact,
            route,
            "Route a clear, bounded `CHECK_FAILURE` directly to one consolidated correction coder.",
        )

    def test_unclear_failure_uses_debugger_before_one_correction(self):
        self.assertIn(
            "For an unclear failure, unexplained behavior, or likely shared root cause, invoke "
            "Debugger before creating one consolidated correction assignment.",
            self.orchestrator_compact,
        )
        self.assertIn("Tester cannot invoke Debugger", self.orchestrator)
        self.assertIn('"debugger": allow', frontmatter(AGENTS / "implementation-orchestrator.md"))
        self.assertIn('"*": deny', frontmatter(AGENTS / "tester.md"))

    def test_tester_has_binary_result_and_exactly_three_routing_reasons(self):
        statuses = re.findall(
            r"^- `status: ([A-Z_]+)`:", self.tester, re.MULTILINE
        )
        reasons = re.findall(r"^- `reason: ([A-Z_]+)`:", self.tester, re.MULTILINE)
        self.assertEqual(statuses, ["PASS", "NOT_PASS"])
        self.assertEqual(reasons, ["CHECK_FAILURE", "INFRASTRUCTURE", "CONFIGURATION"])
        self.assertIn("status: PASS | NOT_PASS", self.tester)
        for obsolete in ("status: FAIL", "INFRA_BLOCKED", "CONFIG_MISSING"):
            self.assertNotIn(obsolete, self.tester)
        self.assertIn("Do not add another status or output-stage field", self.tester)

    def test_tester_rejects_coder_checks_as_matrix_approval(self):
        tester = compact(self.tester)
        self.assertIn(
            "Coder-focused test-first checks and coder reports are non-authoritative development evidence.",
            tester,
        )
        self.assertIn("Do not accept them as Verification Matrix approval", tester)
        self.assertIn("You are the sole authority", tester)

    def test_remote_not_applicable_path_reaches_review_and_cleaner(self):
        self.assert_in_order(
            self.orchestrator_compact,
            "If remote verification is approved as `Not applicable`, one local Tester `PASS` completes",
            "Invoke Code Reviewer only after every applicable Tester invocation is `PASS`.",
            "After `Verdict: APPROVED`, remain in `REVIEWING` and invoke `cleaner`.",
            "Cleaner `PASS` permits final guards.",
            "Only all of these guards permit `DONE`.",
        )

    def test_remote_path_publishes_only_after_local_pass_and_commit(self):
        self.assert_in_order(
            self.orchestrator_compact,
            "Never request push authorization or publish before local Tester `PASS` and successful implementation commit creation.",
            "Publish only the exact locally passed implementation-branch commit",
            "invoke Tester a second time with only the approved remote commands",
            "Require every remote result to identify the exact published implementation commit.",
            "Require both local and remote Tester reports to be `PASS` before review.",
        )

    def test_remote_failure_keeps_commit_and_requires_additive_local_cycle(self):
        self.assertIn(
            "A remote `NOT_PASS` necessarily occurs after a commit exists. Preserve that commit.",
            self.orchestrator_compact,
        )
        self.assertIn(
            "requires the complete local Tester matrix before a new additive, non-amended commit",
            self.orchestrator_compact,
        )
        self.assertIn("Never erase or amend the failed remote commit", self.orchestrator)

    def test_tester_drift_is_guarded_around_precommit_invocation(self):
        self.assert_in_order(
            self.orchestrator_compact,
            "Capture the guarded branch/ref/index/worktree/untracked/metadata snapshot.",
            "Invoke Tester with every required local Verification Matrix command",
            "Compare the guarded snapshot after Tester returns.",
        )
        self.assertIn("unexpected drift is `BLOCKED_OPERATION`", self.state_machine_compact)

    def test_review_requires_every_applicable_tester_pass(self):
        self.assertIn(
            "Invoke Code Reviewer only after every applicable Tester invocation is `PASS`.",
            self.orchestrator,
        )
        self.assertIn("every applicable Tester `PASS` report", self.reviewer)
        self.assertIn("BLOCKED: TESTING_NOT_PASSED", self.reviewer)

    def test_reviewer_accepts_precommit_local_context_and_binds_remote_commit(self):
        reviewer = compact(self.reviewer)
        self.assertIn("not required to claim the later implementation commit", reviewer)
        self.assertIn("remote Tester result must identify the supplied review commit", reviewer)
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
        self.assertIn("Do not edit files, run tests", self.cleaner)
        self.assertIn("diagnose failures, commit, delegate, load skills", self.cleaner)

        invokers = []
        for path in AGENTS.glob("*.md"):
            if '"cleaner": allow' in frontmatter(path):
                invokers.append(path.name)
        self.assertEqual(invokers, ["implementation-orchestrator.md"])

        config = json.loads(read(ROOT / "opencode" / "opencode.jsonc"))
        self.assertEqual(config["subagent_depth"], 1)

    def test_cleaner_scope_and_binary_result_are_bounded(self):
        statuses = set(re.findall(r"status: ([A-Z_]+)", self.cleaner))
        self.assertEqual(statuses, {"PASS", "NOT_PASS"})
        self.assertIn("status: PASS", self.cleaner)
        self.assertIn("status: NOT_PASS", self.cleaner)
        self.assertIn("one consolidated list", self.cleaner)
        self.assertIn("Do not request optional style changes", self.cleaner)
        self.assertIn("changes to untouched infrastructure", self.cleaner)

    def test_cleaner_gets_one_full_correction_cycle_then_blocks(self):
        self.assertIn(
            "A Cleaner `NOT_PASS` containing material simplification findings becomes one consolidated coder correction",
            self.orchestrator_compact,
        )
        self.assertIn(
            "complete local Tester gate, additive commit, applicable remote verification, "
            "Code Review, and Cleaner",
            self.orchestrator_compact,
        )
        self.assertIn("Allow one Cleaner correction only", self.orchestrator)
        self.assertIn(
            "Any later simplification `NOT_PASS` after that budget is consumed is `BLOCKED_IMPLEMENTATION`, including repeated concerns",
            self.orchestrator_compact,
        )
        self.assertIn(
            "Never reset the Cleaner correction budget during an implementation, including for materially different concerns.",
            self.orchestrator_compact,
        )

    def test_cleaner_precondition_failure_blocks_without_using_correction_budget(self):
        self.assertIn(
            "Route it to `BLOCKED_OPERATION`, preserve repository state, and do not consume the Cleaner correction budget.",
            self.orchestrator_compact,
        )
        self.assertIn(
            "precondition failure: MISSING_INPUT | CONTRADICTORY_INPUT | HEAD_MISMATCH",
            self.cleaner,
        )
        self.assertIn("must not be sent to a coder", self.cleaner)

    def test_any_correction_invalidates_prior_evidence_and_approval(self):
        self.assertIn(
            "Any correction invalidates relevant Tester and review evidence and requires the complete local matrix again.",
            self.orchestrator_compact,
        )
        self.assertIn(
            "Any implementation change invalidates prior Tester evidence and review approval.",
            self.orchestrator_compact,
        )

    def test_completion_preserves_default_branch_without_integration(self):
        metadata = frontmatter(AGENTS / "implementation-orchestrator.md")
        self.assertNotIn('"git merge --ff-only *": allow', metadata)
        self.assertIn(
            "The original/default branch must remain exactly at its admitted baseline.",
            self.orchestrator,
        )
        self.assertIn("Do not integrate the default", self.orchestrator)
        self.assertIn("No automatic integration into the default branch occurs", self.state_machine)
        self.assert_in_order(
            self.orchestrator_compact,
            "resolve and capture the default branch/ref and exact tip as the immutable original baseline on every admission",
            "including admission from a non-default branch",
            "If admitted on the default branch, create and switch",
            "If admitted on a clean non-default branch, it must already be that exact approved branch and is used as-is.",
        )
        for destructive in ("git reset", "git clean", "git rebase"):
            self.assertNotIn(f'"{destructive}*": allow', metadata)


if __name__ == "__main__":
    unittest.main()
