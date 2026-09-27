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

## Specification handoff and TDD workflow

The specification process follows a TDD-style handoff:

1. Spec orchestrator prepares a complete implementation package
2. The package is validated using `opencode/scripts/validate_implementation_package.py`
3. The package is passed to the implementation orchestrator for implementation
4. Whether a test is needed is decided from existing coverage and behavior; if warranted, the package defines a test-first ticket and dependent implementation ticket with actual intended red evidence (or explicitly justified prerequisite/exception); otherwise package records reused coverage/justification; regardless, final Tester runs full Verification Matrix.
5. Tests are added incrementally to verify behavior as implementation progresses

## Documentation recommendations

When documentation changes are needed, they should be scoped into a separate
durable documentation ticket rather than being added silently to agent files.
Agent-facing documentation recommendations from `code-pattern` have exact target,
evidence, proposed wording/action, benefit and applicability; adopted immediate
guidance is in package/coder packets, durable docs require explicit scoped ticket;
no silent shared/global edits.

## Implementation Package handoff

Create a complete package using
[`opencode/contracts/implementation-package.md`](opencode/contracts/implementation-package.md).
The user can fill in the template directly, or `spec-orchestrator` can prepare
it. Version 2 requires an `Approach` for every ticket; existing packages must
add this field before `/implement` can accept them. Validate the finished text
before handoff:

```bash
python3 opencode/scripts/validate_implementation_package.py < package.md
```

Select `implementation-orchestrator` and paste the **complete package text**
into its conversation. The agent does not accept paths, issue references, or
raw requests. Commands may prepare package text from another source before
selecting that agent. A structural validator does not replace review of the
requirements. Package readiness does not authorize external writes.

Rerun the installer to link the contract and validator, then restart OpenCode.

### `/implement`

To start implementation from an existing complete package, run either:

```text
/implement owner/repo#42
/implement https://github.com/owner/repo/issues/42
/implement path/to/package.md
```

The command reads the GitHub issue body with `gh` (or the local file), runs the
Implementation Package validator on that text, and passes the complete text
directly to `implementation-orchestrator`. Invalid or unreadable input stops the
handoff. A missing or inaccessible issue returns `BLOCKED_SPEC`; a closed issue
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
python3 scripts/run_tests.py prepare_miravia_issue
python3 scripts/run_tests.py fix_multiple_customers \
  --spec-model openai/gpt-6-sol \
  --implementation-model openai/gpt-6-luna \
  --coder-light-model ovhcloud/qwen3-coder-30b-a3b-instruct \
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
Python repository, asks for a specification package, invokes `/implement`, and
runs the focused `unittest` that the implementation updates.
`github_issue_greeting` fetches the approved package from
`JohnnyVM/opencode-harness#38`, invokes `/implement` with that GitHub reference,
and verifies the isolated implementation, handoff, branch guards, and focused
test. It requires an authenticated `gh` CLI in addition to the normal lifecycle
test prerequisites.
`prepare_miravia_issue` clones `Guadalsistema/connector-proyect` at
`0130a245d35846014372db652acf9d809ac81d0d`, invokes
`/implement Guadalsistema/connector-proyect#10`, and requires all nine tickets, a passing
Tester gate, Reviewer approval, Cleaner pass, a committed clean branch, and
fresh real-Odoo smoke and full runner results. It requires authenticated `gh`,
Go 1.25.5, protoc 31.1, clang-format 18, pinned Go protobuf generators,
rootless Podman, and locally available PostgreSQL 17 and Odoo 17 images.
The four optional model flags select the spec orchestrator, implementation
orchestrator, light coder, and heavy coder independently. Omitted flags retain
their agent defaults. Each model uses the `provider/model` format. The selected
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
restart OpenCode to load `coder-light` and `coder-heavy`.

Instrumented OpenCode tests store raw event streams, session exports, exposed
model reasoning, model usage and timing metrics, `opencode-trace` records, and
`act` output under `artifacts/`. These files may contain prompts, tool data,
source content, or secrets and must not be committed.
