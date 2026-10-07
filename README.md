# opencode-harness

Personal implementation of an OpenCode harness for specification design and
guarded implementation.

## Install

Install the repository configuration into OpenCode's global configuration
directory using the installer script:

```bash
python3 scripts/install.py
```

The installer creates individual absolute symbolic links for exactly these
repository targets:

- `opencode/opencode.jsonc`
- each `opencode/agents/*.md`
- each `opencode/skills/<skill>/` that contains a `SKILL.md` file
- each `opencode/commands/*.md`
- each `opencode/contracts/*.md`
- each `opencode/scripts/*.py`
- each `opencode/plugins/*.js`

It skips existing destinations rather than replacing them. Back up and remove
an existing destination before linking it if needed.

The installer supports a `--dry-run` option to preview changes without
making them:

```bash
python3 scripts/install.py --dry-run
```

Existing files, directories, valid links, and broken links are warned about
and skipped without modification. The installer resolves source paths
independently of the current working directory (cwd-independent). After
installation, restart OpenCode to load the new configuration.

## Conditional agents

Two read-only subagents `test-investigation` and `code-pattern` are conditional
Spec-side advisers, not approval stages. They are not activated by default
and are only used when explicitly requested by the spec orchestrator.

## Three-stage handoff and TDD workflow

The delivery process uses three validated contracts:

1. Spec Orchestrator prepares and validates a Specification Package.
2. `/architect` passes it to the model-neutral Architect, which freezes the
   specification and adds architecture, tickets, and verification in an
   Architecture Package.
3. `/implement` passes that package to Implementation Orchestrator.
4. Implementation Orchestrator creates one validated Coder Assignment per
   ticket before dispatch.
5. Tests are added incrementally; the final Tester runs the complete
   Verification Matrix.

## Documentation recommendations

When documentation changes are needed, they should be scoped into a separate
durable documentation ticket rather than being added silently to agent files.
Agent-facing documentation recommendations from `code-pattern` have exact target,
evidence, proposed wording/action, benefit and applicability; adopted immediate
guidance is in package/coder packets, durable docs require explicit scoped ticket;
no silent shared/global edits.

## Package handoffs

Spec Orchestrator uses
[`opencode/contracts/specification-package.md`](opencode/contracts/specification-package.md).
Validate the finished text before architecture:

```bash
python3 opencode/scripts/validate_specification_package.py < specification.md
```

Run Architect with a local file or GitHub issue and an explicit local output:

```text
/architect path/to/specification.md --output .scratch/architecture.md
/architect owner/repo#42 --output .scratch/architecture.md
/architect https://github.com/owner/repo/issues/42 --output .scratch/architecture.md
```

Architect uses
[`opencode/contracts/architecture-package.md`](opencode/contracts/architecture-package.md),
preserves the complete specification verbatim, and validates its output. It is
model-neutral: its agent configuration does not pin a provider or model.

Implementation Orchestrator creates per-ticket packets using
[`opencode/contracts/coder-assignment.md`](opencode/contracts/coder-assignment.md).
The plugin validates the actual prompt before a coder task can start. Structural
validation does not replace semantic review, and readiness never authorizes
external writes.

Rerun the installer to link the contract and validator, then restart OpenCode.

### `/implement`

To start implementation from an Architecture Package, run either:

```text
/implement owner/repo#42
/implement https://github.com/owner/repo/issues/42
/implement path/to/package.md
```

The command reads the GitHub issue body with `gh` (or the local file), runs the
Architecture Package validator on that text, and passes the complete text
directly to `implementation-orchestrator`. Invalid or unreadable input stops the
handoff. Legacy Implementation Package v2 input is rejected. A missing or
inaccessible issue returns `BLOCKED_SPEC`; a closed issue
pauses before planning and asks the user whether to proceed or stop. GitHub
issue access requires an authenticated `gh` CLI. Install the command and its
plugin with `python3 scripts/install.py`, then restart OpenCode.

## Lifecycle Tests

Run the directory-based lifecycle tests with:

```bash
python3 scripts/run_tests.py
python3 scripts/run_tests.py lifecycle_smoke
python3 scripts/run_tests.py basic_greeting
python3 scripts/run_tests.py github_issue_greeting
python3 scripts/run_tests.py brand_selection
python3 scripts/run_tests.py fix_multiple_customers \
  --spec-model openai/gpt-6-sol \
  --architect-model openai/gpt-6-sol \
  --implementation-model openai/gpt-6-luna \
  --coder-light-model ovhcloud/qwen3-coder-30b-a3b-instruct \
  --coder-medium-model openai/gpt-6-luna \
  --coder-heavy-model openai/gpt-6-luna
python3 scripts/run_tests.py fix_multiple_customers --mcp ripwire
python3 scripts/run_tests.py fix_multiple_customers --no-mcp ripwire
python3 scripts/run_tests.py fix_multiple_customers --clean
```

Each directory under `tests/` that contains a lifecycle phase must provide
`prepare.py`, `run.py`, and `validate.py`. The runner executes those files in
order from the test directory. Each phase receives the same isolated temporary
directory in the `TEST_WORKSPACE` environment variable and a persistent,
git-ignored output directory in `TEST_ARTIFACTS`.
Pass one or more test directory names to run only those tests.
`basic_greeting` is the lowest-cost end-to-end scenario: it creates a local
Python repository, runs Specification, Architecture, and Implementation stages,
and verifies both exact handoffs, the guarded branch, and focused `unittest`.
`brand_selection` clones `git@github.com:Guadalsistema/connector-proyect.git`
at commit `20376ca2a63b5e447258fb9ca4cdc4a63c7593cb`, generates
`docs/spec/brand-selection.md` without questions, invokes `/architect` with its
default `-architecture` output path, and passes that package to `/implement`.
It requires a final `DONE` report with every ticket completed, Tester PASS,
and Code Reviewer approval, alongside exact handoffs and the guarded branch.
This scenario requires repository access through the authenticated `gh` CLI and SSH.
GitHub issue URL and shorthand loading are covered by command integration tests
using local fixtures rather than mutable external issue bodies.
The six optional model flags select the Spec Orchestrator, model-neutral
Architect runtime, Implementation Orchestrator, light coder, medium coder, and heavy coder
independently. In lifecycle tests only, an omitted Architect model inherits the
selected Spec model; the production Architect agent remains unpinned. Other
omitted flags retain their agent defaults. Each model uses the `provider/model`
format. The selected
models are passed to all phases and checked against captured sessions when
those agents run. Repeat the command with different flags to compare runs;
metrics for each run remain in its own timestamped artifact directory.
MCP servers are disabled by default. Use `--mcp NAME` or `--no-mcp NAME` to
explicitly enable or disable a configured server; repeat either option for
multiple servers.
Use `--clean` to delete prior artifact directories for the selected tests
before running them.

After updating the agent names, remove any previously installed global links
for `coder-qwen.md` and `coder-gpt.md`, rerun `python3 scripts/install.py`, and
restart OpenCode to load `coder-light`, `coder-medium`, and `coder-heavy`.

The Implementation Orchestrator starts straightforward tickets with `coder-light`
and complex tickets with `coder-medium` (`openai/gpt-6-luna`). Exhausting light's
attempt budget escalates to medium. Medium has three dispatches per ticket,
including its initial attempt and corrections across later verification/review
cycles; exhaustion escalates to `coder-heavy`. The orchestrator records tier,
remaining attempts, and escalation reasons in its ticket ledger. These dispatch
budgets are separate from a worker's tool-step limit.

Instrumented OpenCode tests store raw event streams, session exports, exposed
model reasoning, model usage and timing metrics, `opencode-trace` records, and
`act` output under `artifacts/`. These files may contain prompts, tool data,
source content, or secrets and must not be committed.
Runtime logs are captured in each stage's `stderr.log`. A zero CLI exit code
does not advance the lifecycle unless the primary session ends with a final
text response; incomplete tool-call sessions stop at their originating stage.
