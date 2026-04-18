# Progress Log

---

## Current Status

**Branch:** `claude/setup-langgraph-project-oXB7j`
**Last updated:** 2026-04-18
**In Progress:** *(none)*
**Next:** デプロイ後に UI レイアウトを確認 / Phase 12 (MCP外部化) or Phase 13 (deepagents)

---

## Step Log

### Step 18 — Phase 17+18: Frontend routing + all CRUD pages (2026-04-15)

Files: `frontend/src/App.tsx`, `frontend/src/styles/theme.ts`,
       `frontend/src/components/{NavBar,PageLayout,Pagination}.tsx`,
       `frontend/src/api/{admin,trades,counterparties,stpExceptions}.ts`,
       `frontend/src/types/{trade,counterparty,stpException}.ts`,
       `frontend/src/pages/{TradeListPage,CounterpartyListPage,CounterpartyEditPage,StpExceptionListPage,StpExceptionCreatePage,TriagePage}.tsx`
- react-router-dom v6 追加, BrowserRouter + Routes に書き換え
- NavBar: Triage/Trades/STP Exceptions/Counterparties リンク + ↺ Reset Data ボタン
- theme.ts: COLOR, CARD, BTN_*, INPUT, LABEL, TABLE 定数
- TradeListPage: trade_id/stp_status/trade_date フィルタ, 20件ページネーション
- CounterpartyListPage/EditPage: lei/name フィルタ, BIC バリデーション付き編集フォーム
- StpExceptionListPage: status/trade_id フィルタ, Triage/Close アクション
- StpExceptionCreatePage: trade_id + error_message フォーム
- TriagePage: PageLayout + 共通テーマに移行, 機能は変更なし

---

### Step 17 — Phase 16: LangGraph tools DB migration (2026-04-15)

Files: `src/infrastructure/tools.py`, `src/infrastructure/db/ssi_repository.py`,
       `src/infrastructure/db/reference_data_repository.py`
- tools.py: _db_session() コンテキストマネージャで DATABASE_URL 有無に応じて DB/mock_store を切り替え
- ssi_repository.py: get(lei, currency, is_external), register() (upsert)
- reference_data_repository.py: get_by_instrument_id()
- 全14ユニットテスト通過（mock_store フォールバック）

---

### Step 16 — Phase 15: Backend CRUD API (2026-04-15)

Files: `src/infrastructure/db/{trade,counterparty,stp_exception}_repository.py`,
       `src/presentation/routers/{trades,counterparties,stp_exceptions,seed}.py`,
       `src/presentation/schemas.py`, `src/main.py`
- TradeRepository: list() with ilike filters, get_by_trade_id()
- CounterpartyRepository: list(), get_by_lei(), update(lei, ...)
- StpExceptionRepository: list(), create(), update_status(), link_triage_run()
- CORS allow_methods: GET/POST/PATCH/OPTIONS に拡張
- POST /api/v1/stp-exceptions/{id}/start-triage: MemorySaver singleton を共有

---

### Step 15 — Phase 14: DB Foundation + Seed (2026-04-15)

Files: `src/infrastructure/db/models.py`, `alembic/versions/0002_add_domain_tables.py`,
       `src/domain/entities.py`, `src/infrastructure/seed.py`, `docker-compose.yml`
- 5 ORM モデル追加: Trade, Counterparty, SettlementInstruction, ReferenceData, StpException
- Alembic 0002: 5 テーブル + インデックス + UniqueConstraint
- TradeStatus / StpExceptionStatus enum + StpException entity 追加
- seed_database() (冪等), reset_and_seed() (TRUNCATE → 再挿入)
- docker-compose command に `python -m src.infrastructure.seed &&` 追加

---

### Step 14 — Phase 10: Secret Manager 抽象化レイヤー (2026-04-13)

Files: `src/infrastructure/secrets.py`, `src/main.py`, `pyproject.toml`, `.env.example`
- secrets.py: `load_secrets()` — SECRET_BACKEND 環境変数で切り替え
  - `env` (デフォルト): .env / os.environ をそのまま使用
  - `gcp`: GCP Secret Manager から取得して os.environ に注入
- pyproject.toml: optional extra `[gcp]` = google-cloud-secret-manager==2.20.2
- main.py: `load_dotenv()` → `load_secrets()` → `setup_logging()` の順序を明示
- .env.example: SECRET_BACKEND / GCP_PROJECT_ID を追加

---

### Step 13 — Phase 9: PostgreSQL DB layer + Alembic (2026-04-11)

Files: `pyproject.toml`, `docker-compose.yml`, `.env.example`, `alembic.ini`,
       `alembic/env.py`, `alembic/script.py.mako`,
       `alembic/versions/0001_initial_schema.py`,
       `src/infrastructure/db/{__init__,models,session,repository}.py`,
       `src/presentation/{router,schemas}.py`
- sqlalchemy==2.0.36, alembic==1.13.3, psycopg2-binary==2.9.9 を追加
- docker-compose: postgres:16 サービス追加; backend が `alembic upgrade head` 後に起動
- SQLAlchemy ORM モデル: TriageRunModel + TriageStepModel (triage_runs / triage_steps)
- session.py: DATABASE_URL 環境変数から遅延初期化、FastAPI Depends 対応
- repository.py: save (insert/upsert by run_id) + list_recent
- Alembic: alembic.ini (placeholder URL) + env.py (DATABASE_URL で上書き) + 初回 migration
- router.py: Depends(get_db) 追加; start/resume 後に DB 保存; GET /api/v1/triage/history 追加
- schemas.py: TriageHistoryResponse 追加
- 単体テスト 34件 引き続き全パス

---

### Step 12 — Phase 8 (partial): Docker test stage (2026-04-11)

Files: `Dockerfile`, `docker-compose.yml`
- Dockerfile: multi-stage build (base → production / base → test)
  - test stage: installs `.[dev]`, copies `tests/`, CMD = pytest
- docker-compose.yml: added `test` service (profile: test)
  - Run with: `docker compose --profile test run test`
- Verified: 34 unit tests pass (Python 3.12, uv venv)

---

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
