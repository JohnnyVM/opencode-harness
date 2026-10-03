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
