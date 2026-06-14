# ADR-0002: Adopt the DDD/BDD/SDD/TDD AI-driven process

- **Status:** Accepted
- **Date:** 2026-06-13
- **Deciders:** Architecture team, PM
- **Supersedes:** none
- **Superseded by:** none

## Context

The project previously used a solo-development workflow: define tasks in
`docs/tasks.md` in plan mode, then develop test-first. This works for one
person but does not scale to a 5–10 person team using AI agents, and it leaves
the design phases (domain modeling, behavior specification, contract
specification) implicit. We want a process where each phase produces a reviewed
artifact that becomes the input to the next phase, with explicit human approval
gates. The process is fully described in `docs/ai-driven-development.md`.

## Decision

We will adopt a four-phase pipeline — DDD → BDD → SDD → TDD — where each phase
is driven by a dedicated agent skill and gated by a human owner:

- DDD artifacts in `docs/domain/` (architect-owned).
- BDD feature files in `features/`, executable in CI (PM-owned).
- SDD artifacts: OpenAPI contract, data-model spec, `spec.feature`
  (architect + engineer owned).
- TDD using the existing red-green-refactor loop in `docs/testing.md`.

We roll this out in three phases (see `docs/ai-driven-development.md` §9). The
governing rule is: **do not create a specification that CI does not execute or
verify.**

## Consequences

- New phase skills live under `.claude/skills/` and are committed.
- BDD requires step definitions and a CI job that executes `.feature` files;
  this is set up incrementally in Phase 1.
- The source of truth for tasks moves from `docs/tasks.md` to GitHub Issues;
  `docs/tasks.md` is demoted to an in-branch scratchpad.
- More up-front review effort per feature, traded against far less rework and
  more reliable agent output, especially with non-frontier models.

## Alternatives considered

- **Keep the `tasks.md` + TDD workflow only.** Rejected: design intent stays
  implicit and the workflow does not support parallel team sessions.
- **Adopt all four disciplines and full tooling at once.** Rejected: high risk
  of the process becoming a formality (document rot). A staged rollout with
  executable gates is safer.
