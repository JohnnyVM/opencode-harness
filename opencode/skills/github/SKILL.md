---
name: github
description: GitHub and gh CLI workflow. Use whenever interacting with GitHub, including issues, pull requests, checks, releases, labels, repositories, GitHub Actions, or GitHub URLs.
---

# GitHub Workflow

Use the `gh` CLI for all GitHub operations. Do not use raw GitHub HTTP APIs,
browser automation, or web scraping when `gh` supports the operation.

Before creating a pull request, inspect `git status`, the complete diff,
recent commits, remotes, and the diff against the intended base branch.

Before committing, inspect `git status`, `git diff`, and `git log --oneline -10`.
Stage only files intended for the commit. Never commit secrets.

Do not commit, amend, push, create pull requests, merge pull requests, or
modify issues unless the user explicitly requests that operation.

When asked to review a pull request, use `gh pr view` and `gh pr diff` to
inspect its metadata, changes, and checks. Report findings first, ordered by
severity with file and line references.

When creating a pull request, verify the base branch, inspect all commits that
will be included, and return the pull request URL after creation.
