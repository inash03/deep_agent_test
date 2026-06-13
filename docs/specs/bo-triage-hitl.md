# Spec: BO triage HITL resume (FR-06)

Specification for starting BO triage and resuming a run that paused for operator
approval. Vocabulary: `docs/domain/glossary.md` (Triage, HITL, Triage Resume).
Behavior: `features/bo_triage_hitl.feature` (business) and
`features/specs/bo_triage_hitl.spec.feature` (detailed). Architecture decision:
ADR-0006 (HITL via `interrupt_before` + persistent checkpointer).

This spec documents already-built behavior captured during the brownfield
retrofit; it is locked by characterization tests in
`tests/bdd/test_bo_triage_hitl.py`.

## Surface

| Aspect | Value |
| --- | --- |
| Start endpoint | `POST /api/v1/trades/{trade_id}/bo-triage` |
| Resume endpoint | `POST /api/v1/trades/{trade_id}/bo-triage/{run_id}/resume` |
| Orchestration | `src/infrastructure/bo_triage_use_case.py` (`BoTriageUseCase`) |
| Graph | `src/infrastructure/bo_agent.py` (`build_bo_graph`) |

## Requests and responses

- Start request (`TriageRequest`): `{ trade_id, error_message }`.
- Resume request (`ResumeRequest`): `{ approved: bool }`.
- Response (`TriageResponse`): `status` is `PENDING_APPROVAL` or `COMPLETED`.
  When `PENDING_APPROVAL`: `run_id`, `pending_action_type`,
  `pending_action_description` are set. When `COMPLETED`: `diagnosis`,
  `root_cause`, `recommended_action`, `action_taken` are set.

The API contract shape is unchanged by this retrofit; see
`docs/api/openapi.json` (the drift test remains green).

## Behavior

1. **Start.** `start()` runs the graph until it either completes or pauses
   `interrupt_before` a HITL node. For a write action (register SSI, reactivate
   counterparty, update SSI, send back to FO) it returns `PENDING_APPROVAL` with
   a `run_id` and `pending_action_type`. Otherwise it returns `COMPLETED`.
2. **Resume — approve.** `resume(run_id, approved=True)` executes the pending
   HITL node (the underlying tool is invoked exactly once), continues to the
   diagnosis, and returns `COMPLETED` with `action_taken = true`.
3. **Resume — reject.** `resume(run_id, approved=False)` injects a rejection
   `ToolMessage` (as the pending node) so the tool is **not** invoked, continues
   to the diagnosis, and returns `COMPLETED` with `action_taken = false`.
4. **Unknown / completed run.** Resuming a missing or already-finished run
   raises `StopIteration`, surfaced by the router as HTTP 404.

## Worked boundary (AG01 — counterparty inactive)

| Step | Outcome |
| --- | --- |
| start with error "AG01" | `PENDING_APPROVAL`, `pending_action_type = reactivate_counterparty` |
| resume approved=true | `COMPLETED`, `action_taken=true`, reactivate tool called 1 time |
| resume approved=false | `COMPLETED`, `action_taken=false`, reactivate tool called 0 times |

## Change protocol

Changing the start/resume contract requires updating this spec and the
`spec.feature`, regenerating `docs/api/openapi.json`
(`uv run python scripts/export_openapi.py`), and keeping the characterization
tests green. The approve/reject resume path must remain covered.
