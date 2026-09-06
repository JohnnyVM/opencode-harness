# opencode-harness

Personal implementation of an OpenCode harness for specification design and
guarded implementation.

## Install

Link the repository configuration into OpenCode's global configuration
directory:

```bash
mkdir -p "$HOME/.config/opencode"
ln -s "$PWD/opencode/opencode.jsonc" "$HOME/.config/opencode/opencode.jsonc"
ln -s "$PWD/opencode/agents" "$HOME/.config/opencode/agents"
ln -s "$PWD/opencode/skills" "$HOME/.config/opencode/skills"
```

These commands fail rather than replace existing destinations. Back up and
remove an existing destination before linking it. Quit and restart OpenCode
after changing configuration, agents, or skills.

See [`docs/agents/agent-workflow.md`](docs/agents/agent-workflow.md) for the
agent map and
[`docs/agents/orchestrator-state-machine.md`](docs/agents/orchestrator-state-machine.md)
for the implementation workflow contract.
