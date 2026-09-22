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

## Implementation Package handoff

Create a complete package using
[`opencode/contracts/implementation-package.md`](opencode/contracts/implementation-package.md).
The user can fill in the template directly, or `spec-orchestrator` can prepare
it. Validate the finished text before handoff:

```bash
python3 opencode/scripts/validate_implementation_package.py < package.md
```

Select `implementation-orchestrator` and paste the **complete package text**
into its conversation. The agent does not accept paths, issue references, or
raw requests. Commands may prepare package text from another source before
selecting that agent. A structural validator does not replace review of the
requirements. Package readiness does not authorize external writes.

Rerun the installer to link the contract and validator, then restart OpenCode.

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
