# Task List

Task state is represented by section position. Do not use checkbox marks for
state. Keep at most one task in `In Progress`.

Completed tasks are archived in `docs/tasks_done.md`.

## In Progress

## Backlog

### Security - Upgrade Next.js to fix middleware bypass vulnerability

Goal: resolve GHSA-26hh-7cqf-hhc6 (high severity), which allows crafted
segment-prefetch requests to bypass Next.js middleware including the
login rate-limiter added in this branch.

Scope:

- Run `npm audit fix` (or manually bump `next` to the patched version)
  inside `frontend/`.
- Verify the rate-limiting middleware still compiles and behaves correctly
  after the upgrade.
- Run `npm run lint` and `npm run build` to confirm no regressions.

Reference: https://github.com/advisories/GHSA-26hh-7cqf-hhc6

### Phase 40 - Disable triage buttons while an event is pending

Goal: prevent manual FO/BO triage from starting while a trade is in
`EventPending`.

Scope:

- Update the trade detail screen to disable `Start FO Triage` and
  `Start BO Triage` when `workflow_status === "EventPending"`.
- Show a concise tooltip or disabled-state reason such as
  `Cannot start triage while an event is pending`.

### Phase 42 - Investigate occasional BO triage 500 errors

Goal: identify and fix cases where `POST /api/v1/trades/{trade_id}/bo-triage`
returns `500 Internal Server Error`.

Known context:

- One candidate reproduction trade is `TRD-009`.
- The error appears when pressing `Start BO Triage`.

Investigation points:

- Backend logs and stack traces.
- `bo_triage.py` use case startup path.
- DB connection and LangGraph checkpoint state.
- LLM/API rate limit handling.

### Phase 36 - Agent tool overview page

Goal: provide an operator-facing page that lists tools available to FO and BO
agents.

Frontend:

- Add an Agent Tools page.
- Display FO and BO tool tables with name, description, and HITL flag.
- Add navigation to the page.

Backend:

- Add `GET /api/v1/agent-tools`.
- Return tool metadata for FO/BO agents.

### Phase 28 - Counterparty search modal for trade creation

Goal: replace the trade input counterparty dropdown with a searchable modal.

Frontend:

- Show selected counterparty as LEI + name.
- Open a modal for counterparty search.
- Support name prefix and partial LEI search.
- Select one result and write it back to the form.

Backend:

- Reuse or extend `GET /api/v1/counterparties` filtering.

### Future - Externalize more tools through MCP

Goal: evaluate which additional LangGraph tools should become MCP-backed
external services.

Considerations:

- Tool ownership and security.
- Local fallback behavior.
- Cloud Run deployment shape.
- Observability and retry behavior.

### Future - Evaluate deepagents

Goal: compare the current LangGraph implementation with a deepagents-based
implementation after the current workflow stabilizes.
