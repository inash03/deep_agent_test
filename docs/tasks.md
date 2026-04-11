# Task List

Task state = section position. No checkbox marks.
Transitions: Backlog → In Progress (before coding) → Done (after commit).
Max 1 task in In Progress at a time.

---

## In Progress

*(none)*

---

## Backlog

### Phase 9 — GCP Database

- GCP Cloud SQL（PostgreSQL）または Firestore のテーブル設計
- `src/infrastructure/` にDB接続クライアント実装（Cloud SQLの場合はSQLAlchemy）
- `mock_store.py` をDBアクセス実装に置き換え（インターフェース変更なし）
- `triage_run_history` テーブル：`TriageResult` の永続化

### Phase 10 — GCP Secret Manager

- GCP Secret Manager に `ANTHROPIC_API_KEY` 等のシークレットを登録
- `src/infrastructure/secrets.py` 実装
- `.env` ファイルによるローカル開発との切り替え
- Cloud Run / GKE サービスアカウントへのアクセス権付与

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
- Phase 11: React Frontend — frontend/ (Vite + React 18 + TypeScript, TriagePage, HITL UI)
- Process improvement: CLAUDE.md task state transitions, tasks.md/progress.md restructure
