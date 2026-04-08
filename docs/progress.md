# Progress Log

---

## Current Status

**Branch:** `claude/setup-langgraph-project-oXB7j`
**Last updated:** 2026-04-08
**In Progress:** Phase 3c — `TriageSTPFailureUseCase`
**Next:** Phase 4 — Presentation Layer (FastAPI)

---

## Step Log

### Step 6 — Process Improvement: CLAUDE.md / tasks.md / progress.md (2026-04-08)

Files: `CLAUDE.md`, `docs/tasks.md`, `docs/progress.md`
- CLAUDE.md: replaced Development Process section with explicit task state transitions and end-of-step checklist
- tasks.md: restructured to section-position-based state (no checkbox marks); corrected all completed tasks to Done
- progress.md: restructured with Current Status at top; Step Log in reverse-chronological order

---

### Step 5 — Phase 3b: LangGraph Agent (2026-04-04)

Files: `src/infrastructure/agent.py`
- `AgentState` TypedDict (messages, trade_id, error_message, action_taken)
- `SYSTEM_PROMPT`: 調査手順・最終出力JSONフォーマット
- `_route_after_agent`: register_ssi → HITL / other tools → read_tools / no calls → END
- `agent_node`, `read_tools_node`, `register_ssi_node`
- `build_graph()`: MemorySaver + interrupt_before=["register_ssi_node"]
- HITL: approve = `invoke(None, config)` / reject = `update_state()` + `invoke(None, config)`

---

### Step 4 — Phase 3a: Mock Store + Tools (2026-04-04)

Files: `src/infrastructure/mock_store.py`, `src/infrastructure/tools.py`
- 5 scenarios: TRD-001 (MISSING_SSI/HITL), TRD-002 (BIC), TRD-003 (CP), TRD-004 (DATE), TRD-005 (INSTR)
- 6 tools: get_trade_detail, get_settlement_instructions, get_reference_data, get_counterparty, lookup_external_ssi, register_ssi
- ALL_TOOLS / READ_ONLY_TOOLS exported

---

### Step 3 — Phase 2: Domain Layer (2026-04-04)

Files: `src/domain/entities.py`, `src/domain/interfaces.py`
- RootCause, TriageStatus enums; STPFailure, TriageResult, Step, TradeDetail, SettlementInstruction, ReferenceData, Counterparty
- ITriageUseCase: start(failure) / resume(run_id, approved)

---

### Step 2 — Phase 1: Project Scaffolding (2026-04-04)

Files: `pyproject.toml`, `src/`, `tests/`, `.env.example`
- Pinned deps: langgraph==1.1.6, langchain-anthropic==1.4.0, fastapi==0.135.3, uvicorn==0.43.0, pydantic==2.12.5, python-dotenv==1.2.2
- Dev: pytest==9.0.2, httpx==0.28.1, ruff==0.15.9, mypy==1.20.0

---

### Step 1 — Use Case Definition (2026-04-04)

- STP Exception Triage Agent に確定
- requirements.md: FR-01〜FR-10, RootCause enum, 6 tools, HITL design, endpoints
- tasks.md: Phase 1〜6 task list

---

### Step 0 — Development Rules Setup (2026-04-03)

Files: `CLAUDE.md`, `docs/progress.md`, `docs/requirements.md`, `docs/tasks.md`
