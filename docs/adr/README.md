# Architecture Decision Records (ADR)

This directory holds the log of significant technical decisions for this
project. The format is intentionally lightweight: one decision per file,
append-only, never rewritten once accepted.

## Why ADRs exist here

AI coding agents do not know *why a design was not chosen*. Without a record,
an agent tends to silently undo earlier decisions when it touches the relevant
code. The ADR log is the durable memory that prevents this. Agents must read
the relevant ADRs before changing a decision they cover, and propose a new
superseding ADR rather than reverting silently.

## Conventions

- File name: `NNNN-short-title.md`, zero-padded sequential number
  (e.g. `0003-use-openapi-as-canonical-contract.md`).
- Copy `0000-template.md` to start a new record.
- Status moves through: `Proposed` → `Accepted` → (optionally)
  `Superseded by ADR-NNNN`.
- A decision is changed by writing a **new** ADR that supersedes the old one.
  Do not edit an accepted ADR except to update its status line.
- `docs/adr/` is owned by the architect via CODEOWNERS; changes require
  architect approval.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-adopt-ddd-bdd-sdd-tdd-process.md) | Adopt the DDD/BDD/SDD/TDD AI-driven process | Accepted |
| [0003](0003-openapi-contract-snapshot-and-drift-test.md) | OpenAPI contract snapshot with drift test | Accepted |
| [0004](0004-model-routing-and-managed-settings.md) | Model routing per phase and managed settings | Accepted |
| [0005](0005-bff-catch-all-proxy.md) | BFF catch-all proxy for browser-to-backend calls | Accepted (retrospective) |
| [0006](0006-hitl-checkpointer.md) | HITL via LangGraph interrupt_before with a persistent checkpointer | Accepted (retrospective) |
| [0007](0007-bo-hybrid-deterministic-react.md) | BO hybrid deterministic + ReAct architecture | Accepted (retrospective) |
| [0008](0008-tasks-as-scratchpad-retire-progress-logs.md) | tasks.md is a pure scratchpad; retire progress.md and tasks_done.md | Accepted |
