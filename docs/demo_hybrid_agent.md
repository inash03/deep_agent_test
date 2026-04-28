# Demo: Hybrid BoAgent — Deterministic + Autonomous Routing

This runbook walks through all 8 test scenarios for the Phase 31 hybrid BoAgent.

## Architecture Summary

```
START → model_router → gather_context → _route_by_triage_path
                                         ├─ AG01        → ag01_handler → reactivate_counterparty (HITL)
                                         ├─ MISSING_SSI → lookup_ssi   → register_ssi (HITL) or escalate
                                         ├─ BE01        → be01_handler → escalate_to_bo_user
                                         ├─ AM04        → fo_side_handler → send_back_to_fo (HITL) or escalate
                                         └─ UNKNOWN/COMPOUND → deep_investigation (LLM ReAct loop)
```

**Cost comparison:**

| Path | LLM calls | Estimated cost (per triage) |
|------|-----------|----------------------------|
| Deterministic (AG01/MISSING_SSI/BE01/AM04) | 1 (summary only, after HITL) | ~$0.002 |
| Autonomous (UNKNOWN/COMPOUND) | 2–5 (ReAct loop) | ~$0.01–0.05 |

---

## Prerequisites

```bash
# Start the API
docker-compose up -d

# Seed the database (includes TRD-013 for AM04 demo)
python -m src.infrastructure.seed
```

---

## Scenario 1 — AG01: Counterparty Inactive (TRD-009)

**Trade:** TRD-009 — `"MT103 rejected by SWIFT. Reason code: AG01."`
**Expected path:** `AG01` → `reactivate_counterparty_node` (HITL pause)

```bash
# 1. Start BO triage
curl -X POST http://localhost:8000/api/v1/trades/TRD-009/bo-triage \
  -H "Content-Type: application/json" \
  -d '{"task_type": "simple"}'
# → returns run_id, pending_action_type="reactivate_counterparty"

# 2. Approve reactivation
RUN_ID="<run_id from above>"
curl -X POST http://localhost:8000/api/v1/trades/TRD-009/bo-triage/$RUN_ID/resume \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
# → triage_complete, 1 LLM call (summary)
```

---

## Scenario 2 — MISSING_SSI (external found): TRD-001

**Trade:** TRD-001 — `"SSI not registered for counterparty 213800QILIUD4ROSUO03 / USD"`
**Expected path:** `MISSING_SSI` → `lookup_ssi` (finds external) → `register_ssi_node` (HITL pause)

```bash
curl -X POST http://localhost:8000/api/v1/trades/TRD-001/bo-triage \
  -H "Content-Type: application/json" \
  -d '{"task_type": "simple"}'
# → pending_action_type="register_ssi"

RUN_ID="<run_id>"
curl -X POST http://localhost:8000/api/v1/trades/TRD-001/bo-triage/$RUN_ID/resume \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

---

## Scenario 3 — MISSING_SSI (external not found): TRD-008

**Trade:** TRD-008 — `"MT103 rejected by SWIFT. Reason code: AC01."`
**Expected path:** `MISSING_SSI` → `ssi_not_found_escalate_node` → `agent` (summary) → END

No HITL pause — escalation happens automatically.

```bash
curl -X POST http://localhost:8000/api/v1/trades/TRD-008/bo-triage \
  -H "Content-Type: application/json" \
  -d '{"task_type": "simple"}'
# → triage_complete immediately (no HITL), escalated to BO user
```

---

## Scenario 4 — BE01: IBAN Format Error (TRD-011)

**Trade:** TRD-011 — `"Custodian HSBC rejected settlement instruction for TRD-011."`
**Expected path:** `BE01` → `be01_handler_node` → `agent` (summary) → END

```bash
curl -X POST http://localhost:8000/api/v1/trades/TRD-011/bo-triage \
  -H "Content-Type: application/json" \
  -d '{"task_type": "simple"}'
# → triage_complete, escalated, 1 LLM call
```

---

## Scenario 5 — AM04, sendback_count=0 (TRD-013)

**Trade:** TRD-013 — `"MT103 rejected by SWIFT. Reason code: AM04."`
**Expected path:** `AM04` → `fo_side_handler_node` (sendback=0) → `send_back_to_fo_node` (HITL)

```bash
# First confirm TRD-013 is seeded with workflow_status=BoAgentToCheck
curl http://localhost:8000/api/v1/trades/TRD-013

curl -X POST http://localhost:8000/api/v1/trades/TRD-013/bo-triage \
  -H "Content-Type: application/json" \
  -d '{"task_type": "simple"}'
# → pending_action_type="send_back_to_fo"

RUN_ID="<run_id>"
curl -X POST http://localhost:8000/api/v1/trades/TRD-013/bo-triage/$RUN_ID/resume \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

---

## Scenario 6 — AM04, sendback_count≥1 (TRD-013 after sendback)

After Scenario 5 completes and FO re-validates, trigger BoAgent again.
`sendback_count` is now 1, so the AM04 path escalates instead.

```bash
curl -X POST http://localhost:8000/api/v1/trades/TRD-013/bo-triage \
  -H "Content-Type: application/json" \
  -d '{"task_type": "simple"}'
# → triage_complete, escalated (sendback prohibited), 1 LLM call
```

---

## Scenario 7 — COMPOUND: Multiple Failures (TRD-010)

**Trade:** TRD-010 — `"Pre-settlement validation failed. Multiple checks not passed."`
**Expected path:** `COMPOUND` → `deep_investigation_node` (LLM ReAct loop)

This uses the autonomous path — the LLM investigates and calls tools.

```bash
curl -X POST http://localhost:8000/api/v1/trades/TRD-010/bo-triage \
  -H "Content-Type: application/json" \
  -d '{"task_type": "complex"}'
# → multiple LLM calls; pending_action_type from LLM decision
```

---

## Scenario 8 — UNKNOWN: SLA Breach (TRD-012)

**Trade:** TRD-012 — `"Settlement SLA breach. Status unknown."`
**Expected path:** `UNKNOWN` → `deep_investigation_node`

```bash
curl -X POST http://localhost:8000/api/v1/trades/TRD-012/bo-triage \
  -H "Content-Type: application/json" \
  -d '{"task_type": "complex"}'
```

---

## Verifying Cost Savings

After running scenarios 1 and 7, compare the `cost_log` in each response:

| Scenario | `cost_log` entries | `total_cost_usd` |
|----------|-------------------|-----------------|
| AG01 (deterministic) | 2 (model_router + agent summary) | ~$0.001–0.003 |
| COMPOUND (autonomous) | 4–8 (model_router + LLM × N) | ~$0.01–0.05 |

Cost data is returned in the `cost_log` field of each triage response.

---

## Running Tests

```bash
# Unit tests — no DB, no LLM (instant)
uv run pytest tests/unit/test_determine_triage_path.py -v
uv run pytest tests/unit/test_gather_context_routing.py -v

# Integration routing tests — no DB, no LLM (mocked)
uv run pytest tests/integration/test_hybrid_routing.py -m integration -v

# Full unit test suite
uv run pytest tests/unit/ -v
```
