# Progress Log

---

## Current Status

**Branch:** `claude/setup-langgraph-project-oXB7j`
**Last updated:** 2026-04-08
**In Progress:** *(none)*
**Next:** Phase 8 partial (Docker unit test) or Phase 9 (GCP DB)

---

## Step Log

### Step 11 — Process improvement: CLAUDE.md / tasks.md / progress.md (2026-04-08)

Files: `CLAUDE.md`, `docs/tasks.md`, `docs/progress.md`
- CLAUDE.md: Development Process section — added explicit task state transitions table and end-of-step checklist
- tasks.md: New structure (section-position-based state, no `[x]` marks); all completed work moved to Done
- progress.md: New structure (Current Status at top; Step Log in reverse-chronological order)

---

### Step 10 — Phase 7 + 8 + 11: Docs / Docker / Frontend (2026-04-06)

Files: `README.md`, `docs/architecture.md`, `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `frontend/`
- CORSMiddleware added to `src/main.py`
- System prompt strengthened (`register_ssi` MUST after `lookup_external_ssi`)
- logging fix: `args` → `tool_args` in extra dict
- README.md: full rewrite (overview, setup, API, tests, Docker, structure)
- docs/architecture.md: Mermaid StateGraph / HITL sequence / Clean Architecture diagrams
- Dockerfile (python:3.12-slim, non-editable install), .dockerignore, docker-compose.yml
- React frontend: Vite 6 + React 18 + TS, TriagePage (input→loading→pending→completed), HITL UI

---

### Step 9 — Phase 6: Observability (2026-04-05)

Files: `src/infrastructure/logging_config.py`, `src/infrastructure/agent.py`, `src/infrastructure/triage_use_case.py`, `src/main.py`
- StructuredFormatter: JSON one-line per log entry (timestamp, level, logger, message + extras)
- agent_node: LLM call count, tool call planned (name + args), final response
- register_ssi_node: HITL-approved registration + completion
- triage start/HITL interrupt/HITL decision/triage complete logged in use case
- setup_logging() called once at app startup

---

### Step 8 — Phase 5: Testing (2026-04-05)

Files: `tests/conftest.py`, `tests/unit/test_tools.py`, `tests/unit/test_entities.py`, `tests/unit/test_output_parsing.py`, `tests/integration/test_triage_api.py`
- 15 unit tool tests (restore_ssi_store fixture for write ops)
- RootCause/TriageStatus/STPFailure/TriageResult/Step validation tests
- _parse_llm_output (5 cases) + _extract_steps (5 cases)
- 6 integration tests (auto-skip if ANTHROPIC_API_KEY not set)
- pyproject.toml: addopts = "-m 'not integration'"

---

### Step 7 — Phase 4: Presentation Layer (2026-04-05)

Files: `src/presentation/schemas.py`, `src/presentation/router.py`, `src/main.py`
- TriageRequest, ResumeRequest, StepOut, TriageResponse (with from_domain())
- POST /api/v1/triage, POST /api/v1/triage/{run_id}/resume
- TriageSTPFailureUseCase singleton via Depends(get_use_case)
- load_dotenv() at startup

---

### Step 6 — Phase 3c: TriageSTPFailureUseCase (2026-04-05)

Files: `src/infrastructure/triage_use_case.py`, `pyproject.toml`
- pyproject.toml: hatchling → setuptools>=68
- start(): UUID → graph.invoke → HITL detect → PENDING_APPROVAL or COMPLETED
- resume(): ToolMessage inject on reject → graph.invoke → COMPLETED
- _parse_llm_output(): last AIMessage JSON + markdown fence strip
- _extract_steps(): AIMessage tool_calls × ToolMessage results → Step list

---

### Step 5 — Phase 3b: LangGraph Agent (2026-04-04)

Files: `src/infrastructure/agent.py`
- AgentState TypedDict (messages, trade_id, error_message, action_taken)
- _route_after_agent: register_ssi → HITL / other → read_tools / none → END
- agent_node, read_tools_node, register_ssi_node
- build_graph(): MemorySaver + interrupt_before=["register_ssi_node"]

---

### Step 4 — Phase 3a: Mock Store + Tools (2026-04-04)

Files: `src/infrastructure/mock_store.py`, `src/infrastructure/tools.py`
- 5 scenarios: TRD-001 (MISSING_SSI/HITL), TRD-002 (BIC), TRD-003 (CP), TRD-004 (DATE), TRD-005 (INSTR)
- 6 tools: get_trade_detail, get_settlement_instructions, get_reference_data, get_counterparty, lookup_external_ssi, register_ssi

---

### Step 3 — Phase 2: Domain Layer (2026-04-04)

Files: `src/domain/entities.py`, `src/domain/interfaces.py`
- RootCause, TriageStatus, STPFailure, TriageResult, Step, TradeDetail, SettlementInstruction, ReferenceData, Counterparty
- ITriageUseCase: start(failure) / resume(run_id, approved)

---

### Step 2 — Phase 1: Project Scaffolding (2026-04-04)

Files: `pyproject.toml`, `src/`, `tests/`, `.env.example`
- langgraph==1.1.6, langchain-anthropic==1.4.0, fastapi==0.135.3, uvicorn==0.43.0, pydantic==2.12.5, python-dotenv==1.2.2

---

### Step 1 — Use Case Definition (2026-04-04)

- STP Exception Triage Agent confirmed
- requirements.md: FR-01〜FR-10, RootCause enum, 6 tools, HITL design, endpoints

---

### Step 0 — Development Rules Setup (2026-04-03)

Files: `CLAUDE.md`, `docs/progress.md`, `docs/requirements.md`, `docs/tasks.md`
