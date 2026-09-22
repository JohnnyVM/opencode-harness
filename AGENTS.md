# Repository Guidance

This repository represents a configuration for opencode.

- Project configuration lives under `opencode/`.
- Skills are stored in `opencode/skills/<skill-name>/SKILL.md`.
- Agents are stored in `opencode/agents/`.
- Direct commands are stored in `opencode/commands/<name>.md`.
- Preserve the existing opencode configuration schema and conventions when making changes.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues; specifications may also be local or direct
input. See `docs/issue-tracker.md`.

### Domain docs

This repository uses a single-context domain documentation layout. See `docs/domain.md`.

## Direct commands

- `/implement <implementation-input>` selects the independent Implementation
  Orchestrator. Exact GitHub Issue References are resolved as durable packages;
  arbitrary input is otherwise accepted directly, including prose, pasted
  package text, multiple or embedded references, and local paths. Embedded
  Issue References are not automatically extracted.

The `/setup-matt-pocock-skills` command is available for explicit user setup of
repository conventions. It is triggered by the user directly, not automatically
by the system.

