# Task List

Task state = section position. No checkbox marks.
Transitions: Backlog → In Progress (before coding) → Done (after commit).
Max 1 task in In Progress at a time.

---

## In Progress

### Phase 14 — DB Foundation + Seed

- 5 つの新 ORM モデル追加 (`src/infrastructure/db/models.py`)
- Alembic migration 0002 作成 (`alembic/versions/0002_add_domain_tables.py`)
- `TradeStatus` / `StpExceptionStatus` / `StpException` エンティティ追加 (`src/domain/entities.py`)
- `src/infrastructure/seed.py` 作成（mock_store.py のデータを DB に挿入）
- `docker-compose.yml` に seed ステップ追加

---

## Backlog

### Phase 15 — Backend CRUD API

- `src/infrastructure/db/trade_repository.py` 作成
- `src/infrastructure/db/counterparty_repository.py` 作成
- `src/infrastructure/db/stp_exception_repository.py` 作成
- `src/presentation/routers/` ディレクトリ以下に trades / counterparties / stp_exceptions / seed ルーター作成
- `src/presentation/schemas.py` に `TradeOut` / `CounterpartyOut` / `StpExceptionOut` 追加
- `src/main.py`: 新ルーター登録 + CORS `allow_methods` 修正

### Phase 16 — LangGraph ツール DB 移行

- `src/infrastructure/db/ssi_repository.py` 作成
- `src/infrastructure/db/reference_data_repository.py` 作成
- `src/infrastructure/tools.py`: `mock_store.*` 呼び出しを DB リポジトリに切り替え

### Phase 17 — フロントエンド共通基盤

- `react-router-dom` + `@types/react-router-dom` を `package.json` に追加
- `src/styles/theme.ts` 作成（共通スタイル定数）
- `src/components/NavBar.tsx` / `PageLayout.tsx` / `Table.tsx` / `Pagination.tsx` 作成
- `src/App.tsx` を `BrowserRouter` + `Routes` に書き換え

### Phase 18 — 各画面実装

- `src/types/trade.ts` + `src/api/trades.ts` + `TradeListPage.tsx`
- `src/types/counterparty.ts` + `src/api/counterparties.ts` + `CounterpartyListPage.tsx` + `CounterpartyEditPage.tsx`
- `src/types/stpException.ts` + `src/api/stpExceptions.ts` + `StpExceptionListPage.tsx` + `StpExceptionCreatePage.tsx`
- `src/api/admin.ts` + NavBar のデータリフレッシュボタン実装

### Phase 11 — Frontend (partial)

- `npm install` + `npm run dev` で動作確認（Node.js 20+ が必要）

### Phase 12 — MCP Server Externalization

- `tools.py` の tool 実装を MCP サーバとして外部化
- LangGraph agent を MCP クライアントとして接続するよう変更
- MCPサーバのDockerコンテナ化
- MCPサーバの認証・認可設計

### Phase 13 — deepagents版（Future）

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
- Phase 3: Infrastructure layer (mock_store.py, tools.py, agent.py, triage_use_case.py)
- Phase 4: Presentation layer (schemas.py, router.py, main.py)
- Phase 5: Testing (unit tests × 3 files, integration tests × 6 cases)
- Phase 6: Observability (logging_config.py, structured logging in agent + use_case)
- Phase 7: Documentation (README.md, docs/architecture.md)
- Phase 8: Containerization — Dockerfile (multi-stage), .dockerignore, docker-compose.yml (+ test service)
- Phase 9: DB layer — SQLAlchemy models, Alembic migration, repository, history endpoint
- Phase 10: Secret Manager abstraction — secrets.py, SECRET_BACKEND 環境変数で .env / GCP 切り替え
- Phase 11: React Frontend — frontend/ (Vite + React 18 + TypeScript, TriagePage, HITL UI)
- Process improvement: CLAUDE.md task state transitions, tasks.md/progress.md restructure
