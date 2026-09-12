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
- each `opencode/skills/<skill>/`
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

Use an approved open GitHub issue as the durable Implementation Package:

```text
/implement #57
/implement owner/repository#57
/implement https://github.com/owner/repository/issues/57
```

The command selects `implementation-orchestrator` as a primary agent and
forwards exactly one Issue Reference. The issue must contain the complete
latest-approved package. `spec-design` remains the default primary agent, and
plain text does not automatically switch primary agents. To use ordinary
`implement #57` text, select `implementation-orchestrator` manually first.

Existing installations link command files individually. Rerun the installer to
add `/implement`, then restart OpenCode.

See [`docs/agents/agent-workflow.md`](docs/agents/agent-workflow.md) for the
agent map and
[`docs/agents/orchestrator-state-machine.md`](docs/agents/orchestrator-state-machine.md)
for the implementation workflow contract.
