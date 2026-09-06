# Agent Workflow

This document is a map of the configured agent structure. The authoritative
orchestrator states and invariants are in
[`orchestrator-state-machine.md`](./orchestrator-state-machine.md).
Agent configuration lives in [`opencode/agents/`](../../opencode/agents/), and
the OpenCode runtime configuration is
[`opencode/opencode.jsonc`](../../opencode/opencode.jsonc).

## End-to-end workflow

```mermaid
flowchart TD
    U([User request]) --> L[Spec Design<br/>discovery and decisions]
    L -->|grilling evidence needed| R[Researcher<br/>focused research]
    R -->|evidence and options| L
    L -->|domain terms or decisions| DM[/domain-modeling/]
    L -->|module boundaries or seams| CD[/codebase-design/]
    L -->|stable draft| TS[/to-spec/]
    TS --> A([User approval and package])
    A --> O[Implementation Orchestrator<br/>independent primary agent]

    O --> SR[SPEC_RECEIVED]
    SR --> P[PLANNING]
    P --> I[IMPLEMENTING]
    I --> C{Choose bounded coder}
    C -->|small mechanical ticket| Q[coder-qwen]
    C -->|complex or subtle ticket| G[coder-gpt]
    Q --> T[TESTING<br/>tester]
    G --> T

    T -->|PASS| RV[REVIEWING<br/>code-reviewer]
    T -->|FAIL| D[DEBUGGING<br/>debugger]
    T -->|CONFIG_MISSING| BS[BLOCKED_SPEC]
    T -->|INFRA_BLOCKED after retry| BI[BLOCKED_IMPLEMENTATION]
    O -.->|lifecycle drift or unsafe operation| BO[BLOCKED_OPERATION]
    D -->|CODE_PROBLEM or TEST_PROBLEM| I
    D -->|DESIGN_SPEC_PROBLEM| BS[BLOCKED_SPEC]
    D -->|ENVIRONMENT_PROBLEM| BI
    D -->|INCONCLUSIVE| BD[BLOCKED_DIAGNOSIS]

    RV -->|APPROVED| F[FINALIZING]
    F -->|lifecycle pass| DONE([DONE])
    F -->|lifecycle failure| BO
    RV -->|CHANGES_REQUIRED, consolidated correction| I
    RV -->|DEBUGGING_REQUIRED| D
    RV -->|TESTING_NOT_PASSED| T
    BS -->|Spec Design resolves specification| A
    BI -->|resolvable| P
    BO -->|operator/user resolves; fresh admission| P
    BS -->|escalate| L
    BI -->|operator action| U
    BO -->|preserve changes and report| U
    BD -->|missing evidence or access| U

    classDef terminal fill:#dcfce7,stroke:#166534;
    class DONE terminal;
```

Spec Design and the Implementation Orchestrator are separate user-facing
primary agents. Spec Design must not implement production code or invoke the
Orchestrator. It produces an approved package that the user supplies to the
Orchestrator. The Orchestrator is the implementation boundary: it schedules at
most one delegated subagent at a time and routes completion or escalation to
the user. The Tester runs the complete local and remote verification matrix and
aggregates all failures from one sweep. The Code Reviewer runs only after the
Tester passes. Delegated agents cannot delegate further.

## Repository lifecycle guard

The Orchestrator admits only an unambiguous clean repository state, validates
the expected branch and tip before every delegation, and preserves work on any
drift. The full admission, commit, remote-verification, fast-forward, and
`BLOCKED_OPERATION` contracts are centralized in
[`orchestrator-state-machine.md`](./orchestrator-state-machine.md).

Native `Task` provides neither timeouts nor isolated-directory routing. These
are not claimed by this workflow; follow-up work should specify external
supervision or an explicitly provisioned isolated environment if needed.

## Configured agents

| Agent | Path | Delegated by | Relevant skills | Notes |
| --- | --- | --- | --- | --- |
| Spec Design | [`opencode/agents/spec-design.md`](../../opencode/agents/spec-design.md) | Primary agent | `grilling`, `grill-with-docs`, `domain-modeling`, `codebase-design`, `to-spec`, `github` | May edit domain, ADR, and specification documents; production edits remain denied. |
| Researcher | [`opencode/agents/researcher.md`](../../opencode/agents/researcher.md) | Spec Design | None | Edit and delegation are denied. Returns evidence, options, unknowns, and follow-up questions. |
| Implementation Orchestrator | [`opencode/agents/implementation-orchestrator.md`](../../opencode/agents/implementation-orchestrator.md) | Primary agent | None | Edit denied; runs at most one leaf worker at a time and owns the state machine. |
| coder-qwen | [`opencode/agents/coder-qwen.md`](../../opencode/agents/coder-qwen.md) | Orchestrator | None | Bounded implementation worker for small mechanical tickets; forced to return after 20 agentic iterations. |
| coder-gpt | [`opencode/agents/coder-gpt.md`](../../opencode/agents/coder-gpt.md) | Orchestrator | None | Bounded implementation worker for complex, cross-module, or subtle tickets. |
| Debugger | [`opencode/agents/debugger.md`](../../opencode/agents/debugger.md) | Orchestrator | None | Diagnostic-only; disposable artifacts may only be written under `/tmp`. |
| Tester | [`opencode/agents/tester.md`](../../opencode/agents/tester.md) | Orchestrator | None | Runs all local and remote checks and returns one consolidated result. |
| Code Reviewer | [`opencode/agents/code-reviewer.md`](../../opencode/agents/code-reviewer.md) | Orchestrator | None | Read-only review after Tester passes; returns one verdict and all findings. |

## Skills and supporting paths

Configured skill definitions are under [`opencode/skills/`](../../opencode/skills/).
The main workflow references these paths:

- Discovery and design: `grilling`, `grill-with-docs`, `domain-modeling`, and `codebase-design`.
- Specification publication: `to-spec` and `github`.
- Repository conventions: [`docs/issue-tracker.md`](../issue-tracker.md) and [`docs/domain.md`](../domain.md).
- Domain context: [`CONTEXT.md`](../../CONTEXT.md); no `docs/adr/` directory currently exists.

## MCP and runtime capabilities

The only MCP server configured in
[`opencode/opencode.jsonc`](../../opencode/opencode.jsonc) is:

| Server | Type and command | Enabled | Repository-local evidence |
| --- | --- | --- | --- |
| `playwright` | Local Podman container: `podman run --rm -i --ipc=host mcp/playwright` | Yes | Configuration only; no MCP implementation or additional server is stored in this repository. |

The default primary agent is `spec-design`, LSP is enabled globally, and
`subagent_depth` is `1`. Spec Design and the Orchestrator are independent
primary agents. The Orchestrator and
Debugger may use `/tmp` and `/tmp/**` as external directories; coders are
denied external-directory access. No other MCP servers, MCP-specific agent
bindings, credentials, or external service paths are declared in the
repository configuration.

## Absence and authority notes

- Worktree-based execution is explicitly out of scope for now; this workflow
  does not define or require worktrees as a feature.
- This map describes configured intent, not a guarantee that every named skill or agent is installed by the runtime.
- `orchestrator-state-machine.md` is the source of truth for Orchestrator states, transitions, and invariants.
- GitHub Issues are the issue/specification surface; operational commands are documented in `issue-tracker.md`.
