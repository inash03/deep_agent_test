# Task List

This file tracks concrete implementation tasks.
Updated by Claude at the end of each development step.

Status: `[ ]` Backlog · `[~]` In Progress · `[x]` Done

---

## Done

- [x] Development rules setup (CLAUDE.md, progress.md, requirements.md, tasks.md)
- [x] Use case definition: STP Exception Triage Agent

---

## Backlog

### Phase 1 — Project Scaffolding

- [ ] Create `pyproject.toml` with pinned dependencies
  - Runtime: `langgraph`, `langchain-anthropic`, `fastapi`, `uvicorn`, `pydantic`
  - Dev: `pytest`, `ruff`, `mypy`, `httpx`
- [ ] Create `src/` directory structure with `__init__.py` files
  - `src/presentation/`
  - `src/domain/`
  - `src/infrastructure/`
- [ ] Create `.env.example` (`ANTHROPIC_API_KEY=`)
- [ ] Verify `.env` is listed in `.gitignore`
- [ ] Create `tests/unit/` and `tests/integration/` directories with `__init__.py`

### Phase 2 — Domain Layer

- [ ] Define `STPFailure` entity (trade_id, error_message)
- [ ] Define `TradeDetail` entity (trade_id, counterparty_lei, instrument_id, currency, amount, value_date)
- [ ] Define `SettlementInstruction` entity (lei, currency, bic, account, iban)
- [ ] Define `TriageResult` entity (trade_id, diagnosis, root_cause: enum, recommended_action, action_taken, steps)
- [ ] Define `RootCause` enum (MISSING_SSI, BIC_FORMAT_ERROR, INVALID_VALUE_DATE, INSTRUMENT_NOT_FOUND, COUNTERPARTY_NOT_FOUND, UNKNOWN)
- [ ] Define `ITriageUseCase` interface (abstract base class)
- [ ] Implement `TriageSTPFailureUseCase` (orchestrates domain logic, calls agent via interface)

### Phase 3 — Infrastructure Layer (LangGraph Agent)

- [ ] Implement mock data store (in-memory dict for trades, SSIs, reference data, counterparties)
- [ ] Define `AgentState` TypedDict for LangGraph state (messages, trade_id, error_message, diagnosis, root_cause, steps, pending_action)
- [ ] Implement read-only tools:
  - [ ] `get_trade_detail(trade_id: str) -> dict`
  - [ ] `get_settlement_instructions(lei: str, currency: str) -> dict`
  - [ ] `get_reference_data(instrument_id: str) -> dict`
  - [ ] `get_counterparty(lei: str) -> dict`
  - [ ] `lookup_external_ssi(lei: str, currency: str) -> dict`
- [ ] Implement write tool: `register_ssi(lei: str, currency: str, ssi_data: dict) -> dict`
- [ ] Implement LangGraph ReAct agent:
  - [ ] `reason` node (LLM decides next tool or finalizes diagnosis)
  - [ ] `act` node (executes tool selected by LLM)
  - [ ] `check_hitl` node (detects if register_ssi is pending → interrupt_before)
  - [ ] conditional edge: continue ReAct loop / finalize / interrupt for HITL
- [ ] Wire up StateGraph with HITL support (`interrupt_before=["check_hitl"]`)

### Phase 4 — Presentation Layer

- [ ] Define `TriageRequest` Pydantic schema (trade_id, error_message)
- [ ] Define `TriageResponse` Pydantic schema (trade_id, diagnosis, root_cause, recommended_action, action_taken, steps, run_id)
- [ ] Define `ResumeRequest` Pydantic schema (approved: bool)
- [ ] Implement `POST /api/v1/triage` router (starts agent run)
- [ ] Implement `POST /api/v1/triage/{run_id}/resume` router (HITL approval/rejection)
- [ ] Create FastAPI app entrypoint (`src/main.py`)
- [ ] Manual smoke test via FastAPI `/docs`

### Phase 5 — Testing

- [ ] Unit test: `get_trade_detail` — existing trade_id
- [ ] Unit test: `get_trade_detail` — unknown trade_id
- [ ] Unit test: `get_settlement_instructions` — SSI found
- [ ] Unit test: `get_settlement_instructions` — SSI not found (triggers MISSING_SSI path)
- [ ] Unit test: `RootCause` enum coverage
- [ ] Integration test: `POST /api/v1/triage` — MISSING_SSI case (no HITL action)
- [ ] Integration test: `POST /api/v1/triage` + `POST /api/v1/triage/{run_id}/resume` — HITL approve
- [ ] Integration test: `POST /api/v1/triage` + `POST /api/v1/triage/{run_id}/resume` — HITL reject

### Phase 6 — Observability

- [ ] Add structured logging (node name + tool name + input/output) at each LangGraph node
- [ ] Include `steps` list in `TriageResponse`

---

## In Progress

*(none)*
