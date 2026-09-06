# Domain Docs

Use a single-context layout by default. Read the root `CONTEXT.md` before
exploring when it exists, then read relevant decisions in `docs/adr/`.

If monorepo signals are present and a multi-context layout is explicitly chosen,
read root `CONTEXT-MAP.md`, each relevant context's `CONTEXT.md`, root
`docs/adr/`, and relevant context-scoped `docs/adr/` paths. Missing files do not
block work. Use the glossary vocabulary and surface conflicts with decisions.

Single-context layout:

```text
CONTEXT.md
```

Multi-context layout:

```text
CONTEXT-MAP.md
src/<context>/docs/adr/
```

Create context or decision directories only when domain work actually requires
them; setup itself does not create them.
