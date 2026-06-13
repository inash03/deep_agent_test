# Progress Log

## Current Status

**Branch:** `claude/enterprise-ai-dev-process-w53dsl`

**Last updated:** 2026-06-13

**Current focus:** AI-driven development process — Phase 1 done, Phase 2 (SDD)
in progress.

**Next:** Apply the full SDD artifact set to one real new feature end-to-end;
decide on Spectral / schemathesis.

## Recent Log

### 2026-06-13 - First full Phase 2 lap: max settlement tenor FO rule (#52)

Branch: `claude/enterprise-ai-dev-process-w53dsl` (PR #51, Issue #52)

Drove one real feature through the full DDD -> BDD -> SDD -> TDD pipeline using
the phase skills, one commit per phase:

- **DDD** (`0045178`): added "Settlement Tenor" / "Maximum Settlement Tenor" to
  `docs/domain/glossary.md`; no model/context-map structure change.
- **BDD** (`1ac84d1`): `features/fo_max_tenor.feature` + step defs (red until TDD).
- **SDD** (`e90cc8a`): `MAX_SETTLEMENT_TENOR_DAYS = 730`, warning severity,
  upper-bound only; `docs/specs/fo-value-date.md` updated and
  `features/specs/fo_max_tenor.spec.feature` added. OpenAPI snapshot regenerated
  with no diff — confirming no API contract change (drift test still green).
- **TDD** (`abcafcd`): unit test first (red, ImportError), then implemented
  `_value_date_within_max_tenor` and registered it in `FO_RULES`.

Verification: `uv run pytest` -> 194 passed, 9 deselected (was 184). New code is
ruff-clean (the 2 remaining F541 findings are pre-existing stubs in the lint
backlog). Backend-only change; frontend build not applicable.

### 2026-06-13 - GitHub integration + Phase 2 (SDD) foundation

Branch: `claude/enterprise-ai-dev-process-w53dsl` (PR #51)

GitHub integration (completing Phase 1):

- `.github/ISSUE_TEMPLATE/feature.yml` + `config.yml`: feature Issue form with
  the artifact checklist (one Issue = one feature = one branch = one session).
- `.github/pull_request_template.md`: requires links to feature/spec/ADR and a
  verification block.
- `.github/CODEOWNERS`: routes `docs/domain/`, `docs/adr/`, `docs/api/`,
  `docs/specs/`, `features/`, and `.claude/` to the architect/PM owner.

Phase 2 (SDD) foundation:

- `scripts/export_openapi.py` + `docs/api/openapi.json`: canonical API contract
  snapshot (27 paths under `/api/v1/*`).
- `tests/unit/test_openapi_contract.py`: drift test (fails if the live app
  diverges from the committed contract) + well-formedness check.
- `docs/specs/fo-value-date.md`: first data-model/rule spec.
- `features/specs/fo_value_date.spec.feature` + `tests/bdd/test_fo_value_date_spec.py`:
  detailed boundary scenarios (6, passing).
- ADR-0003: OpenAPI snapshot + drift-test decision.
- Updated `docs/ai-driven-development.md` rollout table, `CLAUDE.md` status, the
  `/sdd-spec` skill, and `docs/tasks.md` (Phase 2 → In Progress).
- `.github/workflows/ci.yml`: fixed to use `uv sync --extra dev` (the
  `uv pip install --system` form failed on the externally-managed runner).

Verification: `uv run pytest` → 184 passed, 9 deselected.

### 2026-06-13 - AI-driven development process (Phase 1)

### 2026-06-13 - AI-driven development process (Phase 1)

Branch: `claude/enterprise-ai-dev-process-w53dsl`

Added the DDD/BDD/SDD/TDD process for a 5–10 person team using AI agents.

- `docs/ai-driven-development.md` (new): full process — artifacts, ownership,
  agent control files, non-frontier-model strategy, and the staged rollout.
- `docs/adr/` (new): ADR log with `README.md`, `0000-template.md`,
  `0001-record-architecture-decisions.md`, and
  `0002-adopt-ddd-bdd-sdd-tdd-process.md`.
- `docs/domain/` (new): `glossary.md`, `model.md`, `context-map.md`, seeded
  from `src/domain/` and `docs/architecture.md`.
- `features/` (new): executable Gherkin. `fo_value_date_validation.feature`
  with step definitions in `tests/bdd/test_fo_value_date_validation.py`
  bound to the real FO value-date rules (3 scenarios, passing).
- `.claude/skills/` (new): phase skills `ddd-update`, `bdd-feature`,
  `sdd-spec`, `tdd-implement`.
- `.github/workflows/ci.yml` (new): runs ruff + the default pytest suite
  (unit + BDD) on PRs and `main`.
- `pyproject.toml`: added `pytest-bdd==8.1.0` to dev dependencies.
- `CLAUDE.md`: added an index section pointing to the new process and the
  Phase 1 rollout status.

Verification: `uv run pytest` → 176 passed, 9 deselected;
`ruff check tests/bdd/` → clean.

### 2026-05-15 - Auth security hardening

Branch: `claude/enhance-auth-security-YtqHg`

Changes:

- `frontend/src/middleware.ts` (new): IP-based rate limiter on
  `POST /api/auth/callback/credentials` using `@upstash/ratelimit` +
  Upstash Redis (5 req / 10 min / IP; fail-open when Redis is absent).
- `frontend/src/account-lockout.ts` (new): per-username failure counter
  backed by Upstash Redis; locks account 15 min after 5 consecutive
  failures, resets on success.
- `frontend/src/auth.ts`: integrate account lockout checks; fix
  timing-based username enumeration by always running `bcrypt.compare`.
- `docs/requirements.md`: added FR-19, FR-20, three security NFRs, and
  expanded Authentication Requirements with a three-layer defence description.
- `docs/architecture.md`: updated Frontend Architecture table,
  Authentication and BFF section (ASCII flow diagram), and Environment
  Variables to document the new Upstash variables.
- `docs/tasks.md`: added backlog item for Next.js GHSA-26hh-7cqf-hhc6
  middleware-bypass CVE upgrade.

### 2026-05-09 - Documentation refresh

Files:

- `README.md`
- `docs/architecture.md`
- `docs/requirements.md`
- `docs/tasks.md`
- `docs/tasks_done.md`
- `docs/progress.md`
- `docs/demo_hybrid_agent.md`
- `frontend/.env.example`
- `CLAUDE.md`
- `.codex.md`
- `.openai/config.md`

Summary:

- Rewrote the README in Japanese.
- Rewrote project docs in English.
- Removed stale legacy frontend deployment wording.
- Documented the current Next.js App Router, Auth.js, BFF, Vercel, FastAPI,
  Cloud Run, and MCP architecture.
- Added Codex-facing project guidance derived from `CLAUDE.md`.

### 2026-05-09 - Next.js migration branch conflict resolution

Summary:

- Resolved conflicts in the frontend package files, version file, Playwright
  smoke tests, and backend deployment workflow.
- Kept Vercel as the frontend deployment path.
- Kept GitHub Actions focused on Cloud Run backend and MCP server deployment.

### 2026-05-06 - MCP server Cloud Run port hotfix

Summary:

- Updated the MCP external-data server to bind to `0.0.0.0` and use the Cloud
  Run `PORT` environment variable.

### 2026-05-05 - External-data MCP server

Summary:

- Added `mcp_server/` as a Cloud Run service for external market data.
- Added a client/fallback layer in the backend.
- Routed `get_market_fx_rate` through the MCP integration.

## Historical Notes

Older history was previously recorded in this file with mojibake. The important
completed milestones are summarized in `docs/tasks_done.md`.
