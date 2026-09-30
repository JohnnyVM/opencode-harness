---
name: to-spec
description: "Turn the current conversation into a finalized local or issue-tracker spec: no interview, just synthesis of what you've already discussed."
---

Synthesize the already-decided requirements into a complete Specification
Package using the canonical template and rules in
`~/.config/opencode/contracts/specification-package.md`. Do not interview the
user. If a blocking product decision remains unresolved, do not claim the
package is ready. Use project domain vocabulary and respect existing ADRs.

Every completed package has exactly one `status`:

- `SPEC_APPROVED_BY_AGENT` for an evidence-backed complete package without
  explicit user approval of that concrete package.
- `SPEC_APPROVED_BY_USER` only when the user explicitly approved that concrete
  package or authorized its implementation.

Readiness is distinct from authorization for external writes. Record bounded
assumptions and risks rather than guessing product decisions. Include testing
decisions at the highest stable behavioral seam. Do not add architecture,
tickets, file scopes, implementation approaches, or executable commands;
Architect owns those decisions.

Run the read-only validator at
`~/.config/opencode/scripts/validate_specification_package.py` against the
final package text and fix all structural findings before presenting it. The
validator does not replace semantic review of requirements and verification.

When a local file was requested, save the package there. Publication to a
configured issue tracker requires the user's explicit authorization; consult
`docs/issue-tracker.md` and use the `github` skill if applicable. A published or
saved copy is a command source. Present the complete package text or saved path
and direct the user to `/architect <source> --output <architecture-path>`.

Every Specification Package revision invalidates Architecture Packages and
implementation snapshots derived from the earlier text.
