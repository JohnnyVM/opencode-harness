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

## Implement Command

Pass either an exact GitHub Issue Reference or direct implementation input:

```text
/implement #57
/implement owner/repository#57
/implement https://github.com/owner/repository/issues/57
/implement specs/feature.md
/implement Fix the failing customer import and run its existing checks
```

The command selects `implementation-orchestrator` as a primary agent and
forwards all arguments unchanged. When the complete input is an exact
`#<number>`, `<owner>/<repository>#<number>`, or GitHub issue URL, the
Orchestrator resolves that durable package. All other input is handled directly,
including prose, pasted package text, multiple or embedded references, and
local paths. Embedded Issue References are not automatically extracted.

An exact Issue Reference determines the target repository. Direct input uses
the current checkout's unambiguous Git remote. In both cases, the resulting
implementation must be safe to execute. Complete packages are validated before
admission; for raw prose, the Orchestrator resolves executable details during
planning and blocks if a required user decision remains. `spec-orchestrator`
remains the default primary agent, and plain text does not automatically switch
primary agents. Select `implementation-orchestrator` manually before supplying
implementation input outside `/implement`.

Generated local or issue packages contain exactly one readiness field:
`status: SPEC_APPROVED_BY_AGENT` for a complete agent-finalized package, or
`status: SPEC_APPROVED_BY_USER` when the user explicitly approved that concrete
package. Either can start local implementation; external writes still require
separate runtime authorization.

Existing installations link command files individually. Rerun the installer to
add `/implement`, then restart OpenCode.

See [`docs/agents/agent-workflow.md`](docs/agents/agent-workflow.md) for the
agent map and
[`docs/agents/orchestrator-state-machine.md`](docs/agents/orchestrator-state-machine.md)
for the implementation workflow contract.

## Lifecycle Tests

Run the directory-based lifecycle tests with:

```bash
python3 scripts/run_tests.py
python3 scripts/run_tests.py lifecycle_smoke
```

Each directory under `tests/` that contains a lifecycle phase must provide
`prepare.py`, `run.py`, and `validate.py`. The runner executes those files in
order from the test directory. Each phase receives the same isolated temporary
directory in the `TEST_WORKSPACE` environment variable and a persistent,
git-ignored output directory in `TEST_ARTIFACTS`.
Pass one or more test directory names to run only those tests.

Instrumented OpenCode tests store raw event streams, session exports, exposed
model reasoning, model usage and timing metrics, `opencode-trace` records, and
`act` output under `artifacts/`. These files may contain prompts, tool data,
source content, or secrets and must not be committed.
