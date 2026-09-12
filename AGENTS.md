# Repository Guidance

This repository represents a configuration for opencode.

- Project configuration lives under `opencode/`.
- Skills are stored in `opencode/skills/<skill-name>/SKILL.md`.
- Agents are stored in `opencode/agents/`.
- Direct commands are stored in `opencode/commands/<name>.md`.
- Preserve the existing opencode configuration schema and conventions when making changes.
- Orchestrator states and lifecycle rules live in `docs/agents/orchestrator-state-machine.md`.

## Agent skills

### Issue tracker

Issues and specifications are tracked in GitHub Issues. See `docs/issue-tracker.md`.

### Domain docs

This repository uses a single-context domain documentation layout. See `docs/domain.md`.

## Direct commands

- `/implement <issue-reference>` selects the independent Implementation
  Orchestrator to resolve and execute one approved open GitHub issue package.

The `/setup-matt-pocock-skills` command is available for explicit user setup of
repository conventions. It is triggered by the user directly, not automatically
by the system.

`spec-design` remains the default primary agent. Plain text does not
automatically switch primary agents; for ordinary `implement #57` input, first
select `implementation-orchestrator` manually.
