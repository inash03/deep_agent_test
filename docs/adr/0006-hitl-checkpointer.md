# ADR-0006: HITL via LangGraph interrupt_before with a persistent checkpointer

- **Status:** Accepted (retrospective)
- **Date:** 2026-06-13
- **Deciders:** Architecture team (recorded retrospectively)
- **Supersedes:** none
- **Superseded by:** none

## Context

Recorded retrospectively during the brownfield retrofit. Write actions that
change operational data (register SSI, reactivate counterparty, send back to FO,
amend/cancel events) must require explicit human approval (Human-in-the-Loop),
and the paused state must survive a serverless instance restart on Cloud Run.

## Decision

Both agents compile their LangGraph with `interrupt_before` on all HITL nodes
and a shared checkpointer from `src/infrastructure/db/checkpointer.py`:

- `bo_agent.py` interrupts before every node in `_BO_ALL_HITL_NODE_NAMES`
  (deterministic handlers and the deep-investigation tool nodes).
- `fo_agent.py` interrupts before the amend/cancel event nodes.
- `get_checkpointer()` returns a **PostgresSaver** (langgraph-checkpoint-postgres
  over a psycopg3 `ConnectionPool`, `prepare_threshold=0` for Neon/pgBouncer)
  when `DATABASE_URL` is set, and **falls back to MemorySaver** when it is not
  (unit tests / local dev), logging that HITL state will not survive restarts.

HITL resume contract: the caller inspects `get_state().next` to find the pending
node; approval is `graph.invoke(None, config)`; rejection injects a rejection
`ToolMessage` via `graph.update_state(..., as_node=snapshot.next[0])` and then
resumes.

## Consequences

- HITL pauses are durable in production (Postgres), so operator approvals are not
  lost across Cloud Run restarts or load-balancing.
- Unit tests run with an in-memory saver and no database (consistent with the
  harness rules in `docs/testing.md`).
- The resume/approval/rejection path is currently not covered by an automated
  test — a key Tier-1 retrofit gap (see `docs/specs/coverage-matrix.md`).
- A persistent checkpointer adds a Postgres dependency and table setup
  (`PostgresSaver.setup()`), accepted for durability.

## Alternatives considered

- **In-memory checkpointer only.** Rejected for production: serverless restarts
  would drop paused HITL state; kept only as the test/local fallback.
- **Custom approval queue table instead of LangGraph checkpoints.** Rejected:
  duplicates LangGraph's built-in interrupt/resume and state management.
