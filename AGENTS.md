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

## Implementation handoff

Use `opencode/contracts/implementation-package.md` to create a complete
package. Paste its text directly into the Implementation Orchestrator. Commands
may prepare package text from other sources before selecting that agent.

The `/setup-matt-pocock-skills` command is available for explicit user setup of
repository conventions. It is triggered by the user directly, not automatically
by the system.
