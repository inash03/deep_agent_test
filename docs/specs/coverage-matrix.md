# Retrofit coverage matrix

This document maps the existing functional requirements (FR-01 .. FR-20 in
`docs/requirements.md`) to the AI-driven development artifacts that exist today,
so the retrofit of domain/scenario/spec/test/ADR artifacts onto already-built
features is visible, prioritized, and does not produce dead documents.

It is the planning map for brownfield retrofit work. Update it as each gap is
closed.

## Retrofit strategy (how to do this without document rot)

The governing rule is unchanged: **do not create a specification that CI does
not execute or verify.** Applied to existing code:

1. **DDD is mostly done.** The glossary, model, and context map were seeded from
   the code in Phase 1. Extend them by diff only when a retrofit surfaces a new
   concept.
2. **Prioritize, do not sweep.** Retrofit highest-risk / highest-value features
   first (core triage + HITL), not trivial CRUD or dashboards. A full sweep is
   the fastest route to rot.
3. **Be opportunistic too.** Whenever you touch an existing feature, retrofit the
   part you touch first (BDD + spec + characterization test), then change it.
4. **Characterization, not greenfield TDD.** Existing code already works, so
   write tests that *capture current behavior* and BDD that *states intended
   behavior*. Where they diverge, log a bug (Issue/ADR) — do not silently
   encode the divergence as "the spec".
5. **One feature = one Issue = one branch = one PR**, using the phase skills in
   "document existing behavior" mode.
6. **ADRs record decisions, not features.** Retrofit a small number of
   retrospective ADRs for load-bearing past decisions (see below), not one per
   FR.

## FR × artifact coverage

Legend: ✅ exists · ⚠️ partial · ❌ missing.

| FR | Feature | Tests | BDD | spec.feature | Data-model spec | Domain terms |
| --- | --- | --- | --- | --- | --- | --- |
| FR-01 | Create/list trades | ⚠️ `test_api_contracts`, E2E smoke | ❌ | ❌ | ❌ | ✅ |
| FR-02 | Counterparty/SSI/refdata/STP exceptions | ⚠️ `test_tools` (tools only) | ❌ | ❌ | ❌ | ✅ |
| FR-03 | FO rule checks | ✅ `test_fo_rules`, `test_check_rules`, `test_fo_max_tenor` | ✅ | ✅ | ✅ | ✅ |
| FR-04 | BO rule checks | ✅ `test_bo_rules` (pure fns) | ❌ | ❌ | ❌ | ✅ |
| FR-05 | FO triage + HITL | ⚠️ routing/tools only; use-case untested | ❌ | ❌ | ❌ | ✅ |
| FR-06 | BO triage + HITL | ✅ `test_determine_triage_path`, integ `test_hybrid_routing`, `test_bo_triage_hitl` (resume approve/reject) | ✅ | ✅ | ✅ | ✅ |
| FR-07 | Persist triage runs/steps | ⚠️ `test_entities` (domain only); repo/DB untested | ❌ | ❌ | ❌ | ✅ |
| FR-08 | Amend/cancel events + versions | ✅ `test_trade_event_lifecycle` (17) | ❌ | ❌ | ❌ | ✅ |
| FR-09 | Triage history | ❌ E2E smoke only | ❌ | ❌ | ❌ | ✅ |
| FR-10 | Rules/settings/cost dashboards | ⚠️ `test_cost_tracker`; endpoints untested | ❌ | ❌ | ❌ | ⚠️ |
| FR-11 | MCP/external data | ✅ `test_external_data_service`, `test_calendar_service` | ❌ | ❌ | ❌ | ✅ |
| FR-12 | Auth.js single admin | ❌ none | ❌ | ❌ | ❌ | n/a |
| FR-13 | BFF proxy | ❌ none | ❌ | ❌ | ❌ | ✅ |
| FR-14 | Hide BACKEND_API_KEY | ⚠️ `verify_api_key` (backend side) | ❌ | ❌ | ❌ | n/a |
| FR-15 | Vercel deploy | n/a (infra) | n/a | n/a | n/a | n/a |
| FR-16 | Cloud Run deploy | n/a (infra) | n/a | n/a | n/a | n/a |
| FR-17 | English UI / JA Home | ❌ none | ❌ | ❌ | ❌ | n/a |
| FR-18 | Version + SHA display | ❌ none | ❌ | ❌ | ❌ | n/a |
| FR-19 | Login IP rate limit | ❌ none | ❌ | ❌ | ❌ | ✅ (architecture.md) |
| FR-20 | Account lockout | ❌ none | ❌ | ❌ | ❌ | ✅ (architecture.md) |

## Priority tiers for retrofit

**Tier 1 — core domain + HITL (highest risk).** FR-06 BO triage + HITL resume
(**done** — `bo_triage_hitl.feature`, spec, and approve/reject characterization
tests), FR-05 FO triage use-case (untested),
FR-07 triage persistence (DB layer untested), FR-08 events (well unit-tested,
needs BDD + data-model spec).

**Tier 2 — security with zero tests.** FR-19 rate limiting, FR-20 account
lockout, FR-12 auth login. These are defenses with no automated coverage at all.

**Tier 3 — CRUD / reference data.** FR-02 counterparty/SSI/STP-exception
endpoints, FR-04 BO rules (add BDD + data-model spec to match FR-03).

**Tier 4 — dashboards, BFF, UI copy (lower risk).** FR-09, FR-10, FR-11,
FR-13/14, FR-17/18. FR-15/16 are documentation-only.

## Retrospective ADR backlog

Load-bearing decisions embodied in the code. Done so far:

- [x] ADR-0005 — BFF catch-all proxy pattern.
- [x] ADR-0006 — HITL via LangGraph `interrupt_before` + persistent checkpointer.
- [x] ADR-0007 — BO hybrid deterministic + ReAct architecture (FO pure ReAct).

Remaining candidates:

- [ ] MCP-first external data with fail-open direct-ECB fallback.
- [ ] Single-admin Auth.js (Credentials) + Upstash Redis lockout in serverless.
- [ ] Optional RAG augmentation that no-ops when unconfigured.
