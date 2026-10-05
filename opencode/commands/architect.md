---
description: Create an Architecture Package from a specification
agent: architect
subtask: false
---

Usage: `/architect <source> [<local-path> | --output <local-path>]`

The second positional argument and `--output <local-path>` are equivalent. If
neither is supplied, insert `-architecture` before the source's file extension
(or append it if there is no extension). For example, all three commands write
to `docs/specs/brand-selection-architecture.md`:

- `/architect docs/specs/brand-selection.md docs/specs/brand-selection-architecture.md`
- `/architect docs/specs/brand-selection.md --output docs/specs/brand-selection-architecture.md`
- `/architect docs/specs/brand-selection.md`

Quote paths containing spaces when using positional arguments.

The architect command hook validates the specification and supplies its exact text together with the normalized output path.

On a branch other than `main`, `/architect` commits the generated Architecture
Package and its local Specification Package source, then verifies a clean
worktree before the handoff. A GitHub issue source has no local Specification
Package file, so only the generated Architecture Package is committed. The
command never creates a commit on `main` or makes remote writes.
