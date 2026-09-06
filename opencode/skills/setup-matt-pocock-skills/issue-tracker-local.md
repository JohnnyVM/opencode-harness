# Issue tracker: Local Markdown

Issues and specifications live as Markdown files under `.scratch/`.

## Layout

```text
.scratch/<feature-slug>/spec.md
.scratch/<feature-slug>/issues/<NN>-<slug>.md
```

Use one feature directory and one numbered file per issue, starting at `01`.
Each issue has a concise `Status:` line near the top. Record dependencies with
`Blocked by: NN, NN` and append conversation under `## Comments`.

## Lifecycle

Create the feature directory and spec when publishing a specification. Create a
numbered issue file for each ticket. Read the referenced file when fetching a
ticket. Update status and append comments without deleting prior history. Close
an issue by recording its completion and setting its status to `closed`.
