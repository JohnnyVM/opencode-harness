---
name: to-spec
description: "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed."
---

This skill takes the current conversation context and codebase understanding
and produces a stable draft specification. Do not conduct new discovery or
interview the user; synthesize only what has already been decided. If a
required decision is unresolved, record it under Explicit Unknowns.

Read `docs/issue-tracker.md` for the publication workflow and `docs/domain.md`
for domain-document conventions. If either required document is missing, tell the
user to run `/setup-matt-pocock-skills` rather than reporting missing setup. Use the
`github` skill when the configured issue tracker is GitHub.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

2. Record the already-approved seams at which the feature will be tested.
Prefer existing seams to new ones and use the highest stable seam possible. Do
not introduce or ask the user to approve new seams during this synthesis step;
record unresolved seam decisions under Explicit Unknowns.

3. Write the spec using the template below. Publish it to the project issue
tracker only when the user has explicitly authorized creating or updating that
issue. Apply labels only when `docs/issue-tracker.md` explicitly defines them.

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Tickets and Dependencies

A numbered implementation sequence. For every ticket include:

- ticket ID and objective
- dependencies or `None`
- exact allowed files or directories
- forbidden files or directories
- relevant decisions and acceptance criteria

## Acceptance Criteria

A numbered, observable list. Each criterion must be specific enough for the
Tester to determine pass or fail without interpreting product intent.

## Verification Commands

### Local

For every required local check include the exact command, working directory,
prerequisites, and expected successful result. Include tests, builds, static
analysis, and acceptance checks that apply.

### Remote

For every required remote check include:

- setup or publication prerequisite
- exact target remote and ref, with commit identity bound at runtime to the
  Orchestrator's final implementation commit
- exact command used to retrieve or run the check
- expected successful result
- any external-write authorization the Orchestrator needs

If remote verification does not apply, write `Not applicable` with the reason.
Do not omit this section.

## Risks

Known implementation, migration, compatibility, operational, and verification
risks, with mitigations where known. Write `None identified` when appropriate.

## Explicit Unknowns

Every unresolved requirement, decision, dependency, environment constraint, or
verification gap. Write `None` only when the package is complete.

## Out of Scope

A description of the things that are out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>
