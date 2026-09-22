# Issue tracker: GitHub

Issues live in GitHub Issues. Use the `gh` CLI for issue operations and infer
the repository from the Git remote when working inside a clone.

An issue can record a specification, decisions, dependencies, and revisions.
Creating or editing one requires the user's authorization for that external
write. Issue tracking is separate from Implementation Orchestrator intake.

## Conventions

- Create: `gh issue create --title "..." --body "..."`.
- Read: `gh issue view <number> --json number,title,body,state,url`.
- List: `gh issue list --state open --json number,title,body,labels,comments`.
- Comment: `gh issue comment <number> --body "..."`.
- Close: `gh issue close <number> --comment "..."`.

Use native issue dependencies when available, or include
`Blocked by: #<issue>` in the body. A command that retrieves an issue for
implementation must prepare complete package text before the Implementation
Orchestrator is selected; the agent receives only pasted package text.
