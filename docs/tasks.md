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

- [x] Define `STPFailure` entity (trade_id, error_message)
- [x] Define `TradeDetail` entity (trade_id, counterparty_lei, instrument_id, currency, amount, value_date)
- [x] Define `SettlementInstruction` entity (lei, currency, bic, account, iban)
- [x] Define `ReferenceData` entity (instrument_id, description, asset_class, is_active)
- [x] Define `Counterparty` entity (lei, name, bic, is_active)
- [x] Define `Step` entity (step_type, name, input, output, approved) for observability
- [x] Define `TriageResult` entity (trade_id, status, run_id, diagnosis, root_cause, recommended_action, action_taken, steps)
- [x] Define `RootCause` enum (MISSING_SSI, BIC_FORMAT_ERROR, INVALID_VALUE_DATE, INSTRUMENT_NOT_FOUND, COUNTERPARTY_NOT_FOUND, UNKNOWN)
- [x] Define `TriageStatus` enum (COMPLETED, PENDING_APPROVAL)
- [x] Define `ITriageUseCase` interface (start / resume abstract methods)

### Phase 3 — Infrastructure Layer (LangGraph Agent)

- [x] Implement mock data store (`src/infrastructure/mock_store.py`)
  - 5 scenarios: MISSING_SSI, BIC_FORMAT_ERROR, COUNTERPARTY_NOT_FOUND, INVALID_VALUE_DATE, INSTRUMENT_NOT_FOUND
  - External SSI lookup data (TRD-001 → triggers HITL flow)
- [x] Implement read-only tools (`src/infrastructure/tools.py`):
  - [x] `get_trade_detail(trade_id: str) -> str`
  - [x] `get_settlement_instructions(lei: str, currency: str) -> str`
  - [x] `get_reference_data(instrument_id: str) -> str`
  - [x] `get_counterparty(lei: str) -> str`
  - [x] `lookup_external_ssi(lei: str, currency: str) -> str`
- [x] Implement write tool: `register_ssi(lei, currency, bic, account, iban) -> str`
- [x] Define `AgentState` TypedDict for LangGraph state (messages, trade_id, error_message, action_taken)
- [x] Implement LangGraph ReAct agent (`src/infrastructure/agent.py`):
  - [x] `agent_node` (LLM with all tools bound; system prompt injected)
  - [x] `read_tools_node` (ToolNode for read-only tools)
  - [x] `register_ssi_node` (custom node; executes register_ssi after HITL approval)
  - [x] `_route_after_agent` conditional edge (register_ssi → HITL / other tools → read_tools / no calls → END)
- [x] Wire up StateGraph with HITL support (`interrupt_before=["register_ssi_node"]`, MemorySaver)
- [ ] Implement `TriageSTPFailureUseCase` (implements `ITriageUseCase`)

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
