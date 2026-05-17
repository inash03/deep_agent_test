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

### Learning - LLM evaluation pipeline (PromptFoo / Ragas)

Goal: introduce quantitative evaluation of agent judgment quality and RAG
retrieval accuracy.

Scope:

- Define a golden dataset of FO/BO triage cases with expected outcomes.
- Integrate PromptFoo to regression-test prompt changes and tool selection
  in CI.
- Integrate Ragas to measure RAG pipeline quality: context recall, answer
  relevancy, faithfulness.
- Document evaluation metrics and thresholds in `docs/testing.md`.

References:
- https://promptfoo.dev
- https://docs.ragas.io

### Learning - LangGraph checkpointing and streaming

Goal: deepen LangGraph usage by adding persistent checkpoints and real-time
streaming to the frontend.

Scope:

- Replace the current in-memory state with `AsyncPostgresSaver` (Neon) so
  interrupted triage runs can be resumed.
- Expose `astream_events` from FO/BO triage endpoints and pipe the event
  stream to the frontend via Server-Sent Events.
- Show live agent step progress on the trade detail screen.

### Learning - Hybrid RAG (vector + full-text) with reranking

Goal: improve retrieval quality beyond pure vector search.

Scope:

- Add a PostgreSQL `tsvector` full-text search index to `rag_chunks`.
- Implement a hybrid retriever that combines pgvector cosine similarity and
  `ts_rank` scores (RRF or weighted sum).
- Evaluate adding a cross-encoder reranker (e.g. `cross-encoder/ms-marco`
  or Cohere Rerank) as a second-stage filter.
- Compare retrieval quality before and after using the Ragas evaluation
  pipeline.

### Learning - Observability with OpenTelemetry and Langfuse (self-hosted)

Goal: add LLM-aware distributed tracing without sending sensitive trade data
to a third-party SaaS.

Background:
LangSmith is a hosted service that receives full LLM trace payloads. For a
financial application, exporting trade and counterparty data to an external
vendor is a compliance concern. Langfuse is open-source and can be deployed
to Cloud Run inside the same GCP project, keeping all trace data within the
existing trust boundary. OpenTelemetry is the vendor-neutral wire protocol,
so the instrumentation code is not tied to Langfuse and can be swapped later.

Scope:

- Deploy Langfuse (Docker image) as a Cloud Run service backed by the
  existing Neon PostgreSQL instance.
- Instrument the FastAPI backend and LangGraph nodes with the OpenTelemetry
  SDK and the Langfuse exporter.
- Capture: node name, token counts, latency, tool calls, and triage outcome
  per run.
- Verify that no data leaves the GCP project boundary.

### Learning - Multi-agent patterns (Supervisor / Orchestrator)

Goal: extend the current two-agent (FO/BO) design toward a multi-agent
architecture, and compare with deepagents.

Scope:

- Implement a lightweight Supervisor agent that delegates to FO and BO
  subgraphs as LangGraph subgraphs.
- Add a third agent role (e.g. audit or compliance checker) to exercise
  cross-agent handoff.
- Compare the LangGraph implementation with a deepagents-based equivalent
  (see "Evaluate deepagents" below) on the same workflow.

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
