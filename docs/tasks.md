# Task List

Task state is represented by section position. Do not use checkbox marks for
state. Keep at most one task in `In Progress`.

Completed tasks are archived in `docs/tasks_done.md`.

> **Process note:** As part of the AI-driven development process
> (`docs/ai-driven-development.md`), the source of truth for tasks is moving to
> GitHub Issues / Projects (one Issue = one feature = one branch = one agent
> session). This file is being demoted to an in-branch working note. New
> feature work should be tracked as Issues, not added here.

## In Progress

### Process Phase 3 - Subagents, AI review, model routing

Goal: complete the rollout with cross-cutting agents, independent AI review,
and per-phase model routing.

Done so far:

- `.claude/agents/spec-reviewer.md` and `researcher.md` (project subagents).
- `.github/workflows/claude-review.yml` (automatic AI PR review, gated on the
  `ANTHROPIC_API_KEY` secret so CI stays green without it).
- `.claude/settings.json` (shared convenience permission allowlist).
- ADR-0004 (model routing per phase + managed-settings policy).

Remaining:

- Configure the `ANTHROPIC_API_KEY` secret (and optionally the Claude GitHub
  App) so the review workflow activates; set branch protection on `main`.
- Ship the managed (org-level) hard prohibitions described in ADR-0004.
- Decide whether to add Spectral lint and/or schemathesis (integration suite).

Reference: `docs/ai-driven-development.md` §6, §7, §9; ADR-0004.

## Backlog

### Retrofit - Apply DDD/BDD/SDD/TDD artifacts to existing features

Goal: close the artifact gaps on already-built features without document rot.
Map and strategy: `docs/specs/coverage-matrix.md`.

Done so far:

- Coverage matrix (FR-01..FR-20) with priority tiers and retrofit strategy.
- Retrospective ADRs 0005 (BFF proxy), 0006 (HITL checkpointer), 0007 (BO hybrid).

Next (Tier 1, core domain + HITL), one Issue/branch/PR each:

- FR-06 BO triage + HITL resume: BDD + spec.feature + characterization test for
  the approval/rejection resume path (currently untested).
- FR-05 FO triage use-case: characterization tests + BDD/spec.
- FR-07 triage persistence: repository/DB-layer tests.
- FR-08 events: BDD feature + data-model spec (unit tests already strong).

Then Tier 2 (security: FR-19/20/12), Tier 3 (CRUD: FR-02/04), Tier 4 (rest).
Remaining retrospective ADRs: MCP fallback, single-admin Auth.js + Upstash,
optional RAG no-op.

### Process Phase 2 - Adopt SDD (specification-driven design) — done

Completed: committed OpenAPI contract (`docs/api/openapi.json`) with the drift
test, data-model spec (`docs/specs/fo-value-date.md`), detailed scenarios, and
ADR-0003. Validated end-to-end by the first full lap (Issue #52: the
max-settlement-tenor FO rule through DDD -> BDD -> SDD -> TDD). Move to
`tasks_done.md` at the next cleanup.

### CI - Clear ruff backlog and make lint blocking

Goal: `ruff check .` passes repo-wide so the CI lint step can become blocking.

Scope:

- Resolve the existing ruff findings (mostly `E501` line length, plus some
  `F401`/`I001`) across `src/` and `tests/`.
- Once clean, remove `continue-on-error` from the `Lint (ruff, advisory)` step
  in `.github/workflows/ci.yml`.

Reference: introduced with the Phase 1 CI workflow on
`claude/enterprise-ai-dev-process-w53dsl`.

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
