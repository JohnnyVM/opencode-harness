# Design red flags

Challenge a design when it:

- conflicts with the frozen specification or silently expands its scope;
- has fewer than two structurally distinct candidates or a purely cosmetic
  comparison;
- introduces abstractions, adapters, or dependencies without a demonstrated
  variation or need;
- ignores existing repository seams, conventions, tests, or operational limits;
- hides data ownership, control flow, failure behavior, or compatibility impact;
- treats assumptions as facts, or claims reviews/validation that did not occur;
- leaves an implementer unable to identify allowed changes and verification.
