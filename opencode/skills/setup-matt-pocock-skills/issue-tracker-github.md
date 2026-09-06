# Issue tracker: GitHub

Issues and specifications live in GitHub Issues. Use `gh` for issue operations
and infer the repository from the Git remote.

## Conventions

- Create: `gh issue create --title "..." --body "..."`.
- Read: `gh issue view <number> --comments`.
- List: `gh issue list --state open --json number,title,body,labels,comments`.
- Comment: `gh issue comment <number> --body "..."`.
- Close: `gh issue close <number> --comment "..."`.

Pull requests are not an issue request surface. Specifications are published as
issues, and dependencies are recorded with native issue dependencies when
available or as `Blocked by: #<issue>` in the body.

When a skill publishes work, create a GitHub issue. When it fetches a ticket,
read the issue with comments.
