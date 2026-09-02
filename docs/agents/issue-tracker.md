# Issue tracker: GitHub

Issues and specifications live in GitHub Issues. Use the `gh` CLI for issue operations and infer the repository from the Git remote; `gh` does this automatically when run inside a clone.

## Conventions

- **Create**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read**: `gh issue view <number> --comments`.
- **List**: `gh issue list --state open --json number,title,body,labels,comments`, with appropriate `--label` and `--state` filters.
- **Comment**: `gh issue comment <number> --body "..."`.
- **Edit labels**: `gh issue edit <number> --add-label "..."` or `gh issue edit <number> --remove-label "..."`.
- **Close**: `gh issue close <number> --comment "..."`.

Pull requests are not a triage request surface; use GitHub Issues for specifications and tickets.

When a skill says to publish a specification or ticket, create a GitHub issue. Skills publish specifications and tickets as GitHub issues.

When one issue blocks another, use native GitHub issue dependencies when available. Otherwise, include a line such as `Blocked by: #<issue>` in the blocked issue's body.
