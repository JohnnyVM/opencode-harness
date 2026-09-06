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

The `/setup-matt-pocock-skills` command is available for explicit user setup of
repository conventions. It is triggered by the user directly, not automatically
by the system.
