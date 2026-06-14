# GitHub Issue Drafts (staging)

**This is a temporary staging file.** It holds drafts for migrating the former
`docs/tasks.md` backlog to GitHub Issues (the new source of truth: one Issue =
one feature/scenario group = one branch = one agent session — see
`docs/ai-driven-development.md` §5 and ADR-0002/ADR-0008).

Once these are filed as Issues, **delete this file**. Feature drafts follow the
`.github/ISSUE_TEMPLATE/feature.yml` shape; chores/bugs use a lighter shape.

> Already completed, no Issue needed: **Process Phase 2 — Adopt SDD** (OpenAPI
> contract + drift test, data-model spec, ADR-0003; validated end-to-end by the
> first full lap, old Issue #52). Recorded in git history and ADR-0003.

---

## Draft 1 — Process Phase 3: subagents, AI review, model routing

**Labels:** `process`, `enhancement`

**Goal:** complete the AI-driven-process rollout with cross-cutting subagents,
independent AI review, and per-phase model routing.

**Done so far:**
- `.claude/agents/spec-reviewer.md` and `researcher.md` (project subagents).
- `.github/workflows/claude-review.yml` (AI PR review, gated on `ANTHROPIC_API_KEY`).
- `.claude/settings.json` (shared permission allowlist).
- ADR-0004 (model routing per phase + managed-settings policy).

**Remaining (acceptance):**
- [ ] Configure the `ANTHROPIC_API_KEY` secret (and optionally the Claude GitHub
      App) so the review workflow activates.
- [ ] Set branch protection on `main`.
- [ ] Ship the managed (org-level) hard prohibitions described in ADR-0004.
- [ ] Decide whether to add Spectral lint and/or schemathesis (integration suite).

**Notes:** Reference `docs/ai-driven-development.md` §6, §7, §9; ADR-0004.

---

## Draft 2 — Retrofit: apply DDD/BDD/SDD/TDD artifacts to existing features

**Labels:** `retrofit`, `epic`

**Goal:** close artifact gaps on already-built features without document rot.
Map and strategy: `docs/specs/coverage-matrix.md`.

**Done so far:**
- Coverage matrix (FR-01..FR-20) with priority tiers and retrofit strategy.
- Retrospective ADRs 0005 (BFF proxy), 0006 (HITL checkpointer), 0007 (BO hybrid).
- FR-06 BO triage + HITL resume (BDD + spec.feature + data-model spec +
  approve/reject characterization tests).

**Remaining sub-tasks (each its own Issue/branch/PR):**
- [ ] FR-05 FO triage use-case: characterization tests + BDD/spec.
- [ ] FR-07 triage persistence: repository/DB-layer tests.
- [ ] FR-08 events: BDD feature + data-model spec (unit tests already strong).
- [ ] Tier 2 (security: FR-19/20/12).
- [ ] Tier 3 (CRUD: FR-02/04).
- [ ] Tier 4 (remaining FRs).
- [ ] Remaining retrospective ADRs: MCP fallback, single-admin Auth.js + Upstash,
      optional RAG no-op.

**Notes:** This is an epic; split each FR sub-task into its own feature Issue
using `.github/ISSUE_TEMPLATE/feature.yml`.

---

## Draft 3 — CI: clear ruff backlog and make lint blocking

**Labels:** `ci`, `chore`

**Goal:** `ruff check .` passes repo-wide so the CI lint step can become blocking.

**Acceptance:**
- [ ] Resolve existing ruff findings (mostly `E501`, plus some `F401`/`I001`)
      across `src/` and `tests/`.
- [ ] Remove `continue-on-error` from the `Lint (ruff, advisory)` step in
      `.github/workflows/ci.yml`.

**Notes:** Introduced with the Phase 1 CI workflow.

---

## Draft 4 — Security: upgrade Next.js to fix middleware-bypass vulnerability

**Labels:** `security`, `dependencies`

**Goal:** resolve GHSA-26hh-7cqf-hhc6 (high severity) — crafted segment-prefetch
requests can bypass Next.js middleware, including the login rate-limiter.

**Acceptance:**
- [ ] `npm audit fix` (or manually bump `next` to the patched version) in
      `frontend/`.
- [ ] Verify the rate-limiting middleware still compiles and behaves correctly.
- [ ] `npm run lint` and `npm run build` pass with no regressions.

**Notes:** https://github.com/advisories/GHSA-26hh-7cqf-hhc6

---

## Draft 5 — Disable triage buttons while an event is pending (former Phase 40)

**Labels:** `feature`, `frontend`

**User story:** As an operator, I do not want to start FO/BO triage while a trade
is in `EventPending`, so that I do not act on a trade with a pending amendment.

**Acceptance:**
- [ ] `Start FO Triage` and `Start BO Triage` are disabled when
      `workflow_status === "EventPending"`.
- [ ] A concise tooltip/disabled reason such as
      `Cannot start triage while an event is pending` is shown.

---

## Draft 6 — Investigate occasional BO triage 500 errors (former Phase 42)

**Labels:** `bug`, `backend`

**Goal:** identify and fix cases where
`POST /api/v1/trades/{trade_id}/bo-triage` returns `500 Internal Server Error`.

**Known context:**
- Candidate reproduction trade: `TRD-009`; error appears on `Start BO Triage`.

**Investigation points:**
- [ ] Backend logs and stack traces.
- [ ] `bo_triage.py` use-case startup path.
- [ ] DB connection and LangGraph checkpoint state.
- [ ] LLM/API rate-limit handling.

---

## Draft 7 — Agent tool overview page (former Phase 36)

**Labels:** `feature`, `frontend`, `backend`

**User story:** As an operator, I want a page listing the tools available to the
FO and BO agents, so that I understand what each agent can do.

**Acceptance:**
- [ ] Frontend: an Agent Tools page with FO and BO tool tables (name,
      description, HITL flag) and navigation to it.
- [ ] Backend: `GET /api/v1/agent-tools` returns tool metadata for FO/BO agents.

---

## Draft 8 — Counterparty search modal for trade creation (former Phase 28)

**Labels:** `feature`, `frontend`

**User story:** As an operator creating a trade, I want to search counterparties
in a modal instead of a dropdown, so that I can find a counterparty by name or
LEI quickly.

**Acceptance:**
- [ ] Selected counterparty shows as LEI + name.
- [ ] A modal supports name-prefix and partial-LEI search.
- [ ] Selecting one result writes it back to the form.
- [ ] Backend reuses or extends `GET /api/v1/counterparties` filtering.

---

## Draft 9 — Externalize more tools through MCP (future)

**Labels:** `enhancement`, `discussion`

**Goal:** evaluate which additional LangGraph tools should become MCP-backed
external services.

**Considerations:** tool ownership/security, local fallback behavior, Cloud Run
deployment shape, observability and retry behavior.

---

## Draft 10 — Evaluate deepagents (future)

**Labels:** `enhancement`, `discussion`

**Goal:** compare the current LangGraph implementation with a deepagents-based
implementation after the current workflow stabilizes.
</content>
