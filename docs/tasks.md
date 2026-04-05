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
- [x] Manual smoke test via FastAPI `/docs`

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

## Future Backlog

> 動作確認完了後に着手予定。依存関係を考慮して順番を整理済み。

### Phase 7 — Documentation & Diagrams
*依存なし。今すぐ着手可能。*

- [x] `README.md` を更新:
  - プロジェクト概要・ユースケース説明
  - セットアップ手順（install / .env / uvicorn起動）
  - APIエンドポイント一覧と使い方（curl例）
  - テスト実行方法（unit / integration）
- [x] `docs/architecture.md` にMermaid状態遷移図を作成:
  - LangGraph StateGraph の全node/edge（agent → read_tools → register_ssi_node → END）
  - HITLフローの分岐（interrupt_before → approve/reject → resume）
  - Clean Architecture の層構成図

### Phase 8 — Containerization
*Phase 7 完了後。GCPデプロイの前提条件。*

- [x] `Dockerfile` 作成（Python 3.12-slim, uvicorn起動）
- [x] `.dockerignore` 作成
- [x] `docker-compose.yml` 作成（ローカル開発用、.envファイルをマウント）
- [ ] コンテナでのユニットテスト実行確認

### Phase 9 — GCP Database
*Phase 8 完了後。モックデータをDBに置き換える。*

- [ ] GCP Cloud SQL（PostgreSQL）または Firestore のテーブル設計
  - `trades` テーブル、`settlement_instructions` テーブル、`counterparties` テーブル、`reference_data` テーブル
- [ ] `src/infrastructure/` にDB接続クライアント実装（Cloud SQLの場合はSQLAlchemy）
- [ ] `mock_store.py` をDBアクセス実装に置き換え（インターフェース変更なし）
- [ ] `triage_run_history` テーブル：`TriageResult`（run_id, trade_id, root_cause, steps等）を永続化

### Phase 10 — GCP Secret Manager
*Phase 9 完了後（GCPインフラが整った後）。*

- [ ] GCP Secret Manager に `ANTHROPIC_API_KEY` 等のシークレットを登録
- [ ] `src/infrastructure/secrets.py` 実装：`google-cloud-secret-manager` ライブラリで取得
- [ ] `.env` ファイルによるローカル開発との切り替え（環境変数 `USE_SECRET_MANAGER` で制御）
- [ ] `pyproject.toml` に `google-cloud-secret-manager` を追加
- [ ] Cloud Run / GKE サービスアカウントに Secret Manager アクセス権を付与

### Phase 11 — Frontend (React)
*Phase 9〜10 完了後。バックエンドAPIが安定してから着手。*

- [x] React + TypeScript プロジェクトを `frontend/` に作成（Vite）
- [x] トリアージ実行画面: trade_id・error_message入力フォーム
- [x] 結果表示: status / diagnosis / root_cause / recommended_action / steps ビジュアライズ
- [x] HITL承認画面: PENDING_APPROVAL時に pending_action_description を表示し Approve/Reject ボタン
- [x] `frontend/Dockerfile` + `nginx.conf` 作成（docker-compose連携済み）
- [ ] `npm install` + `npm run dev` で動作確認（Node.js 20+ が必要）

### Phase 12 — MCP Server Externalization
*Phase 11 完了後。最も高度な変更。*

- [ ] 現在 `tools.py` に直書きのtool実装を MCP サーバとして外部化
  - 各tool（get_trade_detail, get_settlement_instructions 等）を独立したMCPサーバエンドポイントとして公開
- [ ] LangGraph agent を MCP クライアントとして接続するよう変更
- [ ] MCPサーバのDockerコンテナ化（tool単位 or 機能グループ単位）
- [ ] MCPサーバの認証・認可設計（サービス間通信のセキュリティ）

---

## In Progress

*(none)*
