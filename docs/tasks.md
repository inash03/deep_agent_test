# Task List

Task state = section position. No checkbox marks.
Transitions: Backlog → In Progress (before coding) → Done (after commit).
Max 1 task in In Progress at a time.

---

## In Progress

- Phase 3c: Implement `TriageSTPFailureUseCase` (`src/infrastructure/triage_use_case.py`)

---

## Backlog

### Phase 4 — Presentation Layer

- Define Pydantic schemas: `TriageRequest`, `TriageResponse`, `ResumeRequest` (`src/presentation/schemas.py`)
- Implement `POST /api/v1/triage` router (`src/presentation/router.py`)
- Implement `POST /api/v1/triage/{run_id}/resume` router (`src/presentation/router.py`)
- Create FastAPI app entrypoint (`src/main.py`)
- Manual smoke test via FastAPI `/docs`

### Phase 5 — Testing

- Unit tests: tools (`tests/unit/test_tools.py`) — `get_trade_detail`, `get_settlement_instructions`
- Integration test: COMPLETED flow — TRD-002 BIC_FORMAT_ERROR (`tests/integration/test_triage_api.py`)
- Integration test: HITL approve — TRD-001 MISSING_SSI (`tests/integration/test_triage_api.py`)
- Integration test: HITL reject — TRD-001 MISSING_SSI (`tests/integration/test_triage_api.py`)

### Phase 6 — Observability

- Add structured logging at each LangGraph node (`src/infrastructure/agent.py`)

### Phase 7 — deepagents版（Future）

> LangGraph版完成後に実装。同じユースケースを deepagents で実装し、
> コード量・HITL API・ツール管理の違いを比較する。

- Add `deepagents>=0.5.0a4` and `langchain>=1.2.15` to `pyproject.toml`
- Implement `build_deep_graph()` (`src/infrastructure/agent_deep.py`)
- Implement `TriageDeepSTPFailureUseCase` (`src/infrastructure/triage_use_case_deep.py`)
- Implement `POST /api/v1/triage/deep` + resume endpoint (`src/presentation/router_deep.py`)
- Add `docs/comparison.md` — LangGraph vs deepagents comparison

---

## Done

- Development rules setup (CLAUDE.md, progress.md, requirements.md, tasks.md)
- Use case definition: STP Exception Triage Agent
- Phase 1: Project scaffolding (pyproject.toml, src/ structure, .env.example, tests/)
- Phase 2: Domain layer (entities.py, interfaces.py)
- Phase 3a: Mock data store (`src/infrastructure/mock_store.py`)
- Phase 3b: LangGraph tools + agent (`src/infrastructure/tools.py`, `agent.py`)
