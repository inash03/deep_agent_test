# Task List

Task state = section position. No checkbox marks.
Transitions: Backlog → In Progress (before coding) → Done (after commit).
Max 1 task in In Progress at a time.

---

## In Progress

*(none — 24-B完了。次は 24-A のツール追加)*

---

## Backlog

### Phase 25 — アクセス制御（Basic Auth）

> エージェント呼び出しは LLM コストが発生するため、外部からの無断アクセスを防ぐ。
> フロントエンド（Nginx）とバックエンド（FastAPI）の両方を保護する。

実装内容:
- `.env` / `.env.example` に `APP_USERNAME`, `APP_PASSWORD` を追加
- **フロントエンド**: Nginx 設定に `auth_basic` を追加し、`htpasswd` でパスワードファイルを生成
- **バックエンド**: FastAPI に `HTTPBasic` ミドルウェアを追加（`/docs` と `/health` は除外）
- `docker-compose.yml` でパスワードファイルをマウント

Cloud Run 移行後の発展:
- Cloud IAP（Identity-Aware Proxy）に切り替えると Google アカウントで認証可能

### Phase 24 — エージェント機能増強

#### 24-A: ツールの追加

現在のツール: `get_trade_detail`, `get_settlement_instructions`, `get_reference_data`,
`get_counterparty`, `lookup_external_ssi`, `register_ssi`

追加するツール:
- `reactivate_counterparty(lei)` — `is_active=False` のカウンターパーティを再有効化（HITL 承認対象）
- `update_ssi(lei, currency, **fields)` — 既存 SSI の BIC/口座番号等を修正
- `get_triage_history(trade_id)` — 同一取引の過去トリアージ結果を参照
- `get_counterparty_exception_history(lei)` — 同一カウンターパーティの直近 N 件の STP 失敗件数・傾向
- `escalate(trade_id, reason)` — 自動解決不能と判断した場合に担当者エスカレーション（新 HITL タイプ）

#### 24-B: 複雑・曖昧なシナリオの追加 ✅ 完了

追加済みシナリオ（TRD-008〜012）:

| Trade ID | エラーメッセージ | 真の原因 | root_cause |
|---------|-----------------|---------|------------|
| TRD-008 | `MT103 rejected by SWIFT. Reason code: AC01. Sender BIC: ACMEGB2L.` | SSI の口座番号が古い | SWIFT_AC01 |
| TRD-009 | `MT103 rejected by SWIFT. Reason code: AG01. Counterparty LEI: 213800XYZINACTIVE001.` | カウンターパーティ非アクティブ | SWIFT_AG01 |
| TRD-010 | `Pre-settlement validation failed for TRD-010. Multiple checks not passed.` | SSI 未登録 かつ CP 非アクティブ | COMPOUND_FAILURE |
| TRD-011 | `Custodian HSBC rejected settlement instruction for TRD-011. No further details provided.` | SSI の IBAN フォーマット誤り | IBAN_FORMAT_ERROR |
| TRD-012 | `Settlement confirmation not received within SLA window for TRD-012. Status unknown.` | BIC が失効（調査困難） | UNKNOWN |

システムプロンプトに SWIFT コード知識（AC01/AG01/AM04/BE01）、is_active チェック、IBAN/BIC 検証ガイダンスを追加済み。

#### 24-C: アクション多様化（HITL の拡張）

現在の HITL: SSI 登録の承認/却下（1種類）

追加する HITL パターン:
- カウンターパーティ再アクティブ化の承認
- 複数の修正案を提示して人間が選択（例:「A: SSI を更新する / B: エスカレーションする」）
- エスカレーション通知の確認

#### 24-D: パターン分析

- `get_counterparty_exception_history` の結果を使い、同一カウンターパーティで直近 30 日間に 3 件以上の失敗があれば警告メッセージを diagnosis に含める
- 過去に同じ root_cause で解決済みのトリアージがあれば、その解決策を推奨アクションに反映する

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

### Phase 21 — GCP read-only IAM ロールと MCP 連携（低優先度・保留）

> **保留理由**: Web版 Claude Code は Anthropic の VM 上で動作するため、GCP サービスアカウントキーを
> そこに置くことはセキュリティ上好ましくない（read-only でもクラウドリソース情報が露出するリスク）。
> デスクトップ版 Claude Code を使う環境が整ったタイミングで再検討する。
> GCP MCP サーバーが公式に成熟した場合も再検討対象。

- GCP サービスアカウント `claude-reader` 作成済み（`claude-reader@<project>.iam.gserviceaccount.com`）
  - 付与ロール: `roles/compute.viewer`, `roles/logging.viewer`, `roles/monitoring.viewer`, `roles/run.viewer`
- サービスアカウントキー（JSON）生成済み・VM に保管済み
- 残り作業: `~/.claude/settings.json` に `GOOGLE_APPLICATION_CREDENTIALS` を設定（デスクトップ版環境で実施）

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
- Phase 22 前半: VM への自動デプロイ — GitHub Actions + SSH、environment: GCP_VM、concurrency で多重実行防止
- Phase 20: バックエンドを Cloud Run に移行 — entrypoint.sh、Artifact Registry、2ジョブ workflow（Cloud Run + VM SSH）
- Phase 25: アクセス制御 — Nginx Basic Auth（フロント）+ API キー（バックエンド LLM エンドポイント）
