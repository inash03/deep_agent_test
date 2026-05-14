# Testing Guide

This document defines how this project uses test-driven development and test
harnesses. It is written for both human developers and AI coding agents.

The guiding rule is simple: tests should be derived from business and
functional requirements, not from the current implementation. Existing code is
evidence, not the source of truth.

## Goals

- Make the STP exception triage workflow safe to change.
- Let agents run the test-write-run-fix cycle autonomously.
- Keep default tests deterministic, fast, and free from real external services.
- Make requirement coverage and known gaps visible.
- Prevent "done" reports before relevant tests pass.

## Test Pyramid

Use the smallest test layer that can prove the requirement.

| Layer | Purpose | Default location | External dependencies |
| --- | --- | --- | --- |
| Unit | Domain rules, pure functions, routing decisions, request validation | `tests/unit/` | None |
| Service / use case | Workflow orchestration with fake repositories and fake clients | `tests/unit/` or `tests/integration/` depending on dependencies | Fakes by default |
| API contract | Status codes, request validation, auth gates, response shapes | `tests/unit/test_api_contracts.py` or focused API tests | Fake DB/session |
| Integration | Real DB, real LLM, real MCP, or deployed-service behavior | `tests/integration/` | Explicit opt-in |
| E2E | Critical operator flows through the Next.js UI | `frontend/tests/e2e/` | Local dev server and test credentials |

Default `pytest` must stay safe for local and CI execution without real Neon,
Anthropic, OpenAI, Cloud Run, ECB, or MCP access.

## Mandatory TDD Workflow

For every behavior change:

1. Pick the requirement or user-visible behavior.
2. Identify the closest existing test file or create a focused new one.
3. Write the smallest failing test that expresses the requirement.
4. Run the focused test and confirm it fails for the expected reason.
5. Implement the smallest production change that satisfies the test.
6. Run the focused test until it passes.
7. Run the relevant full suite.
8. Refactor only while tests are green, rerunning affected tests after changes.

Documentation-only changes may skip new tests, but still require a reasonable
verification step such as reviewing rendered Markdown or running unaffected
smoke checks when practical.

## Harness Strategy

### Database

- Unit tests must not connect to Neon PostgreSQL.
- Prefer fake repositories, `MagicMock` sessions, transaction-scoped fixtures,
  or pure schema/request tests.
- Tests requiring a real database must live under `tests/integration/` and be
  marked `integration`.
- Default `pytest` excludes integration tests through `pyproject.toml`.

### LLM Providers

- Unit tests must not call Anthropic or OpenAI.
- Stub model clients, LangGraph nodes, embeddings, cost trackers, and agent
  tools at infrastructure boundaries.
- Assert deterministic outputs: routing decisions, root causes, HITL pauses,
  tool selections, state transitions, persistence calls, and cost-log shape.
- Real provider tests must be opt-in integration tests with explicit
  environment requirements.

### MCP and External APIs

- Unit tests must not call Cloud Run MCP servers, ECB, or other network APIs.
- Use fake clients or monkeypatched responses.
- Test fallback behavior explicitly when the external service is unavailable.
- Keep calendar, FX, SSI lookup, and market-data behavior deterministic in the
  default suite.

### HTTP and Auth

- Browser-facing code must call the BFF at `/api/backend/*`.
- FastAPI protected endpoints must validate `X-API-Key` when `API_KEY` is set.
- Local development may leave `API_KEY` unset; tests should cover both modes.
- Auth.js session-required behavior belongs in E2E or frontend integration
  tests because the enforcement happens in Next.js.

### Time, IDs, and Environment

- Freeze or inject dates for date-sensitive rule tests.
- Use deterministic IDs and seed-like fixtures.
- Patch environment variables inside tests instead of relying on the caller's
  shell.
- Tests should leave process-global state clean for later tests.

## Requirement Coverage Matrix

This matrix describes current coverage at a practical level. It should be
updated when major requirements or tests change.

| Requirement | Expected behavior | Current coverage |
| --- | --- | --- |
| FR-01 Create and list trades | Trade creation validates required economic fields and server owns `trade_id` allocation | `tests/unit/test_api_contracts.py`, repository/API coverage still partial |
| FR-02 Manage counterparties, SSI, reference data, and STP exceptions | CRUD-like business data screens and APIs behave consistently | Partial; mostly repository/router behavior remains a gap |
| FR-03 Run FO rule checks | FO checks produce deterministic pass/fail results and workflow status | `tests/unit/test_check_rules.py`, `tests/unit/test_rule_engine_auto_triage.py` |
| FR-04 Run BO rule checks | BO checks validate counterparty, SSI, BIC/IBAN, and workflow status | `tests/unit/test_check_rules.py`, `tests/unit/test_rule_engine_auto_triage.py` |
| FR-05 Start and resume FO triage with HITL | Agent write actions pause for human approval | Partial via routing/tool tests; dedicated FO HITL use-case tests are still needed |
| FR-06 Start and resume BO triage with HITL | Register SSI, reactivate counterparty, and send-back paths require approval | `tests/unit/test_determine_triage_path.py`, `tests/unit/test_gather_context_routing.py`, partial integration coverage |
| FR-07 Persist triage runs, steps, diagnoses, and root causes | Triage history and observability records are saved in expected shape | Partial; repository persistence tests are still needed |
| FR-08 Manage amend/cancel trade events and versions | AMEND/CANCEL have explicit validation and approval lifecycle | `tests/unit/test_api_contracts.py`, more lifecycle tests still needed |
| FR-09 Show triage history | API/UI can list persisted triage outcomes | Partial; needs API contract and UI coverage |
| FR-10 Show rules, settings, and cost dashboards | Cost and settings data are summarized accurately | `tests/unit/test_cost_tracker.py`, route/UI coverage still partial |
| FR-11 Use MCP/external data lookup | External-data behavior has deterministic fallback without network | `tests/unit/test_external_data_service.py`, `tests/unit/test_calendar_service.py` |
| FR-12 Auth.js single administrator login | Login accepts configured credentials and rejects invalid credentials | E2E/auth coverage still needed |
| FR-13 Browser calls through BFF | Browser API clients use `/api/backend/*` | Frontend API client tests still needed |
| FR-14 Hide backend API key from browser | No `BACKEND_API_KEY` exposure in client bundles or `NEXT_PUBLIC_*` | Static/security test still needed |
| FR-15 Vercel frontend deployment | Frontend builds successfully from `frontend/` | `npm run build` / direct Next build verification |
| FR-16 Cloud Run backend/MCP deployment | Backend deployment workflows package expected services | CI workflow tests still needed |
| FR-17 English UI text except optional Japanese Home view | Business UI uses English copy | Manual/visual review; UI text tests optional |
| FR-18 Display version and short commit SHA | Frontend version display uses package version and Vercel SHA | Frontend test coverage still needed |

## Known Test Gaps

These are the highest-value gaps to close next:

- API contract tests for list/detail/update routes:
  - trades
  - counterparties
  - SSI
  - STP exceptions
  - settings
  - cost
- Trade Event lifecycle tests:
  - creating AMEND creates a pending version
  - FO rejection cancels and removes pending amendment version
  - BO approval activates amended version
  - CANCEL approval sets trade status to `Cancelled`
- FO and BO triage use-case tests:
  - pending approval response shape
  - resume approved/rejected behavior
  - persistence and cost-log failure should not break API response
- Frontend/BFF tests:
  - browser-side clients call `/api/backend/*`
  - BFF forwards `X-API-Key` only server-side
  - protected pages and `/api/backend/*` require Auth.js session
- Secret exposure tests:
  - no `BACKEND_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY` in client code
  - no secret values in committed config or fixtures
- E2E operator flows:
  - login
  - create trade
  - run FO/BO checks
  - inspect triage history
  - approve/reject an event

## Commands

Backend default suite:

```bash
pytest
```

When `pytest` is not on `PATH`, use the local virtual environment:

```bash
.\.venv\Scripts\python.exe -m pytest
```

Focused backend examples:

```bash
.\.venv\Scripts\python.exe -m pytest tests\unit\test_api_contracts.py -v
.\.venv\Scripts\python.exe -m pytest tests\unit\test_check_rules.py -v
.\.venv\Scripts\python.exe -m pytest tests\unit\test_gather_context_routing.py -v
```

Integration tests:

```bash
.\.venv\Scripts\python.exe -m pytest tests\integration -m integration -v
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
npm run test:e2e
```

If `npm` is not on `PATH` in the Codex desktop runtime, call the bundled Node.js
binary with the local package entrypoints.

## Completion Criteria

A task is not complete until:

- The requirement-driven test exists or a clear reason for not adding one is
  documented.
- The focused test passes.
- The relevant full suite passes.
- Any skipped integration or E2E test is explicitly called out.
- The final report lists exact commands run and pass/fail status.

