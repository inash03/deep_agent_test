# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-06-13
- **Deciders:** Architecture team
- **Supersedes:** none
- **Superseded by:** none

## Context

The project is moving to an AI-driven development process in which coding agents
make and apply changes across sessions. Agents have no memory of *why* a design
was chosen or rejected, and they tend to undo earlier decisions when they touch
the relevant code. We need a durable, reviewable record of significant
decisions that both humans and agents can read.

## Decision

We will keep Architecture Decision Records under `docs/adr/`, one decision per
file, numbered sequentially, append-only. A decision is changed only by writing
a new ADR that supersedes the old one. Conventions are documented in
`docs/adr/README.md`.

## Consequences

- New significant technical decisions require an ADR before or with the PR that
  implements them.
- Agents must read relevant ADRs before altering a decision they cover.
- `docs/adr/` is protected by CODEOWNERS (architect approval) once branch
  protection is configured in Phase 1/2.
- A small, ongoing documentation cost in exchange for stable design intent.

## Alternatives considered

- **No formal record (rely on commit messages / PR descriptions).** Rejected:
  not discoverable by agents, and intent is scattered and lost over time.
- **A single growing "decisions.md".** Rejected: merge conflicts under
  concurrent edits and no clear supersession model.
