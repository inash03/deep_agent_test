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
- [x] Implement `TriageSTPFailureUseCase` (implements `ITriageUseCase`)

### Phase 4 — Presentation Layer

- [x] Define `TriageRequest` Pydantic schema (trade_id, error_message)
- [x] Define `TriageResponse` Pydantic schema (trade_id, status, diagnosis, root_cause, recommended_action, action_taken, steps, run_id)
- [x] Define `ResumeRequest` Pydantic schema (approved: bool)
- [x] Implement `POST /api/v1/triage` router (starts agent run)
- [x] Implement `POST /api/v1/triage/{run_id}/resume` router (HITL approval/rejection)
- [x] Create FastAPI app entrypoint (`src/main.py`)
- [ ] Manual smoke test via FastAPI `/docs`

### Phase 5 — Testing

**Unit tests (no LLM — run with `pytest`):**
- [x] `tests/unit/test_tools.py`: all 6 tools (get_trade_detail, get_settlement_instructions, get_reference_data, get_counterparty, lookup_external_ssi, register_ssi)
- [x] `tests/unit/test_entities.py`: RootCause enum, STPFailure validation, TriageResult, Step
- [x] `tests/unit/test_output_parsing.py`: _parse_llm_output (valid JSON, markdown fence, fallback), _extract_steps (single/multiple tools, register_ssi HITL type, empty, missing result)
- [x] `tests/conftest.py`: integration marker registration

**Integration tests (requires ANTHROPIC_API_KEY — run with `pytest -m integration`):**
- [x] `tests/integration/test_triage_api.py`:
  - [x] TRD-002: BIC_FORMAT_ERROR → COMPLETED (no HITL)
  - [x] TRD-003: COUNTERPARTY_NOT_FOUND → COMPLETED (no HITL)
  - [x] TRD-001: MISSING_SSI → PENDING_APPROVAL
  - [x] TRD-001: HITL approve → COMPLETED, action_taken=True
  - [x] TRD-001: HITL reject → COMPLETED, action_taken=False
  - [x] unknown run_id → 404

### Phase 6 — Observability

- [x] Add `src/infrastructure/logging_config.py`: JSON structured formatter + `setup_logging()`
- [x] Add logging to `agent.py` nodes:
  - `agent_node`: LLM呼び出し、tool call計画（tool名・args）、最終応答
  - `register_ssi_node`: SSI登録実行（HITL承認後）+ 完了
- [x] Add logging to `triage_use_case.py`:
  - triage開始（run_id, trade_id, error_message）
  - HITL中断（run_id, trade_id）
  - HITL決定受信（run_id, approved）
  - triage完了（run_id, root_cause, action_taken, step_count）
- [x] `src/main.py` で `setup_logging()` を起動時に呼び出し
- [x] `steps` リストは TriageResponse に含まれている（Phase 4 完了済み）

---

## In Progress

*(none)*
