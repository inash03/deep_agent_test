# Progress Log

## Current Status

**Branch:** `claude/enterprise-ai-dev-process-w53dsl`

**Last updated:** 2026-06-13

**Current focus:** AI-driven development process — Phase 1 done, Phase 2 (SDD)
in progress.

**Next:** Apply the full SDD artifact set to one real new feature end-to-end;
decide on Spectral / schemathesis.

## Recent Log

### 2026-06-14 - Reorganize agent guides as maps, not manuals

Branch: `claude/lucid-einstein-mwupcd`

Applied the "map, not a manual" principle to the agent instruction files. Slimmed
`CLAUDE.md` from 272 to ~90 lines (a documentation map + golden rules), and
aligned the sibling mirrors `.codex.md` and `.openai/config.md` to the same lean
form. Externalized the detailed rules that had no home into new `docs/`:

- `docs/development.md` (process, task tracking, checklist, git, commands).
- `docs/frontend.md` (App Router rules, UI language, versioning).
- `docs/backend.md` (layering, API compatibility).
- `docs/security.md` (secrets, key roles, boundaries).
- `docs/README.md` (top-level documentation index).

Sections that already had a source of truth (architecture, TDD/harness,
AI-driven process) are now references instead of duplicates, removing the stale
"Phase 1" rollout status the mirrors had drifted into.

### 2026-06-13 - Retrofit lap: FR-06 BO triage HITL resume

Branch: `claude/enterprise-ai-dev-process-w53dsl` (PR #51)

First Tier-1 brownfield retrofit lap through DDD -> BDD -> SDD, closing the
previously-untested BO triage resume (approve/reject) path.

- DDD: added "Triage Resume" to `docs/domain/glossary.md`.
- BDD: `features/bo_triage_hitl.feature` (approve / reject business scenarios).
- SDD: `features/specs/bo_triage_hitl.spec.feature` (AG01 boundary, outline) and
  data-model/contract spec `docs/specs/bo-triage-hitl.md`. OpenAPI unchanged.
- Tests: `tests/bdd/test_bo_triage_hitl.py` — 5 characterization scenarios
  driving the real `BoTriageUseCase` with all boundaries mocked (no DB/LLM/
  network). Approve executes the reactivate tool once + `action_taken=true`;
  reject skips the tool + `action_taken=false`.
- Updated coverage matrix (FR-06 now BDD/spec/data-model ✅), tasks.

No production code changed (characterization of existing behavior).
Verification: `uv run pytest` -> 199 passed, 9 deselected (was 194).

### 2026-06-13 - Brownfield retrofit: coverage matrix + retrospective ADRs

Branch: `claude/enterprise-ai-dev-process-w53dsl` (PR #51)

Started retrofitting the AI-driven artifacts onto existing features.

- `docs/specs/coverage-matrix.md` (new): maps FR-01..FR-20 to existing tests /
  BDD / spec.feature / data-model specs, with the retrofit strategy
  (characterization over greenfield TDD; prioritize core+HITL; no full sweep)
  and a priority tiering. Built from a `researcher` subagent survey.
- Retrospective ADRs (decisions already embodied in code, verified against
  source before writing):
  - ADR-0005 BFF catch-all proxy (`route.ts`).
  - ADR-0006 HITL via `interrupt_before` + persistent PostgresSaver checkpointer
    with MemorySaver fallback (`db/checkpointer.py`). Corrected the survey's
    "in-memory only" claim after reading the code.
  - ADR-0007 BO hybrid deterministic + ReAct, FO pure ReAct (`bo_agent.py`,
    `fo_agent.py`).
- Updated the ADR index.

No code changed; `uv run pytest` still 194 passed. Next: a Tier-1 behavioral
retrofit lap (BO/FO triage + HITL) using the phase skills in
"document-existing-behavior" mode.

### 2026-06-13 - Phase 3 foundation: subagents, AI review, model routing

Branch: `claude/enterprise-ai-dev-process-w53dsl` (PR #51)

- `.claude/agents/spec-reviewer.md` (new): independent, read-only reviewer that
  checks a change against its SDD artifacts and conventions (model: opus).
- `.claude/agents/researcher.md` (new): read-only codebase researcher for
  context isolation (model: sonnet).
- `.github/workflows/claude-review.yml` (new): automatic AI PR review using
  `anthropics/claude-code-action@v1`, gated on the `ANTHROPIC_API_KEY` secret via
  an env-mapped step check so CI stays green when the secret is absent. Note: the
  secret cannot be referenced in a job/step `if:`, hence the step-based gate.
- `.claude/settings.json` (new): shared convenience permission allowlist only
  (test/lint/read-only git + the OpenAPI export script; denies force-push). No
  behavior-changing hooks.
- ADR-0004 (new): model routing per phase + managed-settings policy.
- Updated `docs/ai-driven-development.md` (§6, §9), `CLAUDE.md`, ADR index.

Verification: workflow + agent frontmatter + settings.json all parse cleanly;
`uv run pytest` unaffected (194 passed).

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
