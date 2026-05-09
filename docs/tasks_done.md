# Done Tasks Archive

This file is an append-only summary of completed work. New active work belongs
in `docs/tasks.md`.

- Phase 1: Project scaffolding with `pyproject.toml`, `src/`, `.env.example`,
  and tests.
- Phase 2: Domain layer with triage entities and interfaces.
- Phase 3: Initial LangGraph agent, mock store, tools, and triage use case.
- Phase 4: FastAPI presentation layer for initial triage endpoints.
- Phase 5: Unit and integration test foundation.
- Phase 6: Structured JSON logging for agent and use-case execution.
- Phase 7: Initial README and architecture documentation.
- Phase 8: Dockerfile and Docker Compose test profile.
- Phase 9: PostgreSQL, SQLAlchemy, and Alembic foundation.
- Phase 10: Secret loading abstraction for local env and GCP Secret Manager.
- Phase 11: Initial React frontend.
- Phase 15-18: CRUD APIs and UI pages for trades, counterparties, SSI,
  reference data, and STP exceptions.
- Phase 20-22: Cloud Run backend deployment through GitHub Actions.
- Phase 24-26: FO/BO workflow states, rule engine, LangGraph FO/BO agents,
  trade events, settings, and detailed trade UI.
- Phase 29-35: `stp_status` removal, model/cost tracking, hybrid deterministic
  and autonomous BoAgent routing, rules page, cost dashboard, and LLM cost logs.
- Phase 38: Legacy `/api/v1/triage` chain removal and FO/BO triage history
  consolidation.
- Phase 39: Trade detail rule-result display fixes.
- Phase 41: RAG support with pgvector and OpenAI embeddings.
- Phase 43: BoValidated-to-Done transition fix.
- Phase 44: Counterparty name display and slash-formatted instrument IDs.
- Phase 45: Playwright smoke tests.
- Phase 46: IBAN checksum validation and ECB FX rate tool.
- Phase 12 Step 1: External-data MCP server for `get_market_fx_rate`.
- Hotfix: Cloud Run port binding fix for the MCP server.
- Next.js migration: migrated the legacy SPA frontend to Next.js App Router,
  Auth.js, Vercel hosting, and a Next.js BFF.
- Documentation refresh: rewrote docs after the Next.js migration and unified
  documentation language rules.
