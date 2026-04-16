# Task List

Task state = section position. No checkbox marks.
Transitions: Backlog → In Progress (before coding) → Done (after commit).
Max 1 task in In Progress at a time.

---

## In Progress

*(none)*

---

## Backlog

### Ops — GCP 静的外部 IP の予約（人間作業）

> VM を再起動するたびに外部 IP が変わる問題の恒久対策。
> e2-micro VM に割り当てている間は無料枠に含まれる（VM 停止中は課金あり）。

手順（Cloud Shell または gcloud から実行）:
```bash
# 1. 静的 IP を予約
gcloud compute addresses create stp-agent-ip --region=us-central1

# 2. 予約した IP アドレスを確認
gcloud compute addresses describe stp-agent-ip --region=us-central1

# 3. VM の既存エフェメラル IP を解除
gcloud compute instances delete-access-config free-dev-vm \
  --access-config-name="External NAT" --zone=us-central1-a

# 4. 静的 IP を VM に割り当て
gcloud compute instances add-access-config free-dev-vm \
  --access-config-name="External NAT" \
  --address=<上記で確認した IP> \
  --zone=us-central1-a
```

完了後は `.env` の `VITE_API_URL` と `CORS_ORIGINS` を新しい固定 IP に更新する。

### Phase 20 — バックエンドを Cloud Run に移行

- Artifact Registry リポジトリを作成（`gcloud artifacts repositories create`）
- バックエンド用 Cloud Run サービスを作成（リージョン: us-central1、メモリ: 512Mi〜1Gi）
- 環境変数（`DATABASE_URL`, `ANTHROPIC_API_KEY`, `SECRET_BACKEND` 等）を Secret Manager 経由で設定
- `CORS_ORIGINS` をフロントエンドの URL（VM の外部 IP またはカスタムドメイン）に更新
- `docker-compose.yml` からバックエンドサービスを削除し、フロントエンドのみに簡略化
- フロントエンドの `VITE_API_URL` を Cloud Run の URL（`https://xxx.run.app`）に更新
- MemorySaver 注意点: Cloud Run はステートレス → `min-instances=1` で回避（将来は DB ベースの checkpointer に移行）

### Phase 22 — CI/CD パイプライン（GitHub Actions + Cloud Run）

> Azure DevOps + self-hosted agent の経験があれば概念は同じ。
> GitHub Actions の hosted runner が Cloud Build の hosted agent に相当。

パイプラインのトリガーとフロー:
```
push to main
  → GitHub Actions workflow
    → Docker build（バックエンドイメージ）
    → push to Artifact Registry
    → Cloud Run に新リビジョンをデプロイ
```

実装タスク:
- `.github/workflows/deploy-backend.yml` を作成
  - トリガー: `push` to `main`（`src/` 配下の変更のみ）
  - ステップ: Workload Identity Federation で認証 → `docker build` → `docker push` → `gcloud run deploy`
- GCP 側の事前設定（人間作業）:
  - Workload Identity Pool + Provider の作成（サービスアカウントキーファイル不要の推奨認証方式）
  - GitHub Actions に `WORKLOAD_IDENTITY_PROVIDER` と `SERVICE_ACCOUNT` の secrets を登録
- フロントエンド（静的ファイル）は将来的に Cloud Storage + Cloud CDN に移行することで VM も不要にできる

### Phase 21 — GCP read-only IAM ロールと MCP 連携

- GCP サービスアカウント `claude-reader` を作成
  - 付与ロール: `roles/compute.viewer`, `roles/logging.viewer`, `roles/monitoring.viewer`, `roles/run.viewer`
- サービスアカウントキー（JSON）を生成・保管
- `~/.claude/settings.json` に `GOOGLE_APPLICATION_CREDENTIALS` 環境変数を設定
- 動作確認: Claude Code から `gcloud compute instances list` などが実行できること
- （将来）GCP 用 MCP サーバが成熟したら移行を検討

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

### Phase 23 — フロントエンドを Firebase Hosting に移行（低優先度）

> Azure Blob Storage の静的ホスティングに相当。VM が不要になり HTTPS も無料。
> Phase 20（Cloud Run 移行）と Phase 22（CI/CD）完了後に検討。

- Firebase プロジェクトを作成（GCP プロジェクトと連携可能）
- `firebase.json` と `.firebaserc` を追加
- `frontend/` に `firebase deploy` でデプロイできることを確認
- SPA ルーティング対応: `firebase.json` に `"rewrites": [{"source": "**", "destination": "/index.html"}]` を設定
- CI/CD への組み込み: GitHub Actions に `firebase-action/deploy` ステップを追加
- `VITE_API_URL` を Cloud Run の URL に固定し、VM への依存をなくす

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
- Phase 14: DB Foundation + Seed — 5 ORM models, Alembic 0002 migration, seed.py, TradeStatus/StpExceptionStatus entities
- Phase 15: Backend CRUD API — trade/counterparty/stp_exception repositories + routers, schemas, CORS fix
- Phase 16: LangGraph tools DB migration — tools.py DB/mock fallback, ssi_repository, reference_data_repository
- Phase 17+18: Frontend routing + all CRUD pages — NavBar, PageLayout, Pagination, TradeListPage, CounterpartyListPage/EditPage, StpExceptionListPage/CreatePage, theme.ts
- Phase 19: DB を Neon PostgreSQL に移行 — postgres コンテナ削除、DATABASE_URL を外部化
