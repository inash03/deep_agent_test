# Task List

This file tracks concrete implementation tasks.
Updated by Claude at the end of each development step.

Status: `[ ]` Backlog · `[~]` In Progress · `[x]` Done

---

## Done

- [x] Development rules setup (CLAUDE.md, progress.md, requirements.md, tasks.md)
- [x] Use case definition: FX Trade Confirmation Matching Agent

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

- [ ] Define `FxTrade` entity (Pydantic model: currency_pair, notional, rate, dates, BIC, payment_instructions)
- [ ] Define `MatchResult` entity (status: MATCHED/MISMATCHED, mismatches list, swift_draft)
- [ ] Define `IMatchingUseCase` interface (abstract base class)
- [ ] Implement `MatchFxTradeUseCase` (orchestrates domain logic, calls agent via interface)

### Phase 3 — Infrastructure Layer (LangGraph Agent)

- [ ] Define `AgentState` TypedDict for LangGraph state
- [ ] Implement tool: `compare_fx_fields(our_trade, counterparty_trade) -> list[MismatchedField]`
- [ ] Implement tool: `generate_mt300_draft(our_trade, mismatches) -> str`
- [ ] Implement node: `validate_input` (runs Pydantic validation)
- [ ] Implement node: `compare_fields` (calls compare_fx_fields tool)
- [ ] Implement node: `generate_swift_draft` (calls generate_mt300_draft tool)
- [ ] Implement node: `output` (assembles final MatchResult)
- [ ] Wire up StateGraph with conditional edge (MATCHED → output, MISMATCHED → generate_swift_draft → output)

### Phase 4 — Presentation Layer

- [ ] Define `MatchRequest` Pydantic schema (wraps two FxTrade)
- [ ] Define `MatchResponse` Pydantic schema (status, mismatches, swift_draft, steps)
- [ ] Implement `POST /api/v1/match` router
- [ ] Create FastAPI app entrypoint (`src/main.py`)
- [ ] Manual smoke test via FastAPI `/docs`

### Phase 5 — Testing

- [ ] Unit test: `compare_fx_fields` — all fields match
- [ ] Unit test: `compare_fx_fields` — rate mismatch
- [ ] Unit test: `compare_fx_fields` — value_date mismatch
- [ ] Unit test: `generate_mt300_draft` — output contains required MT300 tags
- [ ] Integration test: `POST /api/v1/match` — MATCHED case
- [ ] Integration test: `POST /api/v1/match` — MISMATCHED case with swift_draft

### Phase 6 — Observability

- [ ] Add structured logging (node name + input/output) at each LangGraph node
- [ ] Include `steps` list in `MatchResponse`

---

## In Progress

*(none)*
