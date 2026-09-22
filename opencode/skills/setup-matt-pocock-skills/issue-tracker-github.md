# Issue tracker: GitHub

Issues live in GitHub Issues. Use `gh` for issue operations and infer the
repository from the Git remote. Creating or editing an issue requires the
user's external-write authorization. An issue can record a specification and
its revision history; it is not input to the Implementation Orchestrator.

## Conventions

- Create: `gh issue create --title "..." --body "..."`.
- Read: `gh issue view <number> --json number,title,body,state,url`.
- List: `gh issue list --state open --json number,title,body,labels,comments`.
- Comment: `gh issue comment <number> --body "..."`.
- Close: `gh issue close <number> --comment "..."`.

Record dependencies with native issue dependencies when available or
`Blocked by: #<issue>` in the body. A command may prepare complete package
text from an issue before selecting the Implementation Orchestrator; the agent
receives only pasted package text.
