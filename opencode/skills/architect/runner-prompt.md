# Architecture runner prompt

Use after receiving a validated Specification Package. Produce version 2 only;
version 1 is retired:

> Preserve the package verbatim in the final Frozen Specification section.
> Produce the exact ordered v2 structure in the Architecture Package contract:
> decision-first summary, evidence-backed repository findings, at least two
> structurally distinct candidates, explicit comparison/recommendation, proposed
> design, interfaces/behavior, implementation tickets, testing strategy,
> runnable verification matrix, complete AC→D/T/L traceability, risks/open
> questions, and frozen specification last. Use stable C/D/T/L identifiers.
> Keep sections concise and non-repetitive. Do not implement production code or
> change the specification. Write only to the explicitly supplied output path,
> validate the v2 package (including byte-preservation when the source path is
> available), and report structural validation separately from design review.
> Do not claim independent or multi-model review unless it actually happened.
