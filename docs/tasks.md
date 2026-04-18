# Task List

Task state = section position. No checkbox marks.
Transitions: Backlog → In Progress (before coding) → Done (after commit).
Max 1 task in In Progress at a time.

---

## In Progress

#### Phase 26-B — ルールエンジン実装

**目的:** FoCheck / BoCheck のルールを定義し、取引データに対して実行する。

**Backend:**
- `src/domain/check_rules.py` 新規
  - `FoCheckRule` / `BoCheckRule` の定義（rule_name, description, check_fn）
  - FoCheck 7 ルール実装（trade_date_not_future, trade_date_not_weekend, value_date_after_trade_date, value_date_not_past, value_date_settlement_cycle, amount_positive, settlement_currency_consistency）
  - BoCheck 7 ルール実装（counterparty_exists, counterparty_active, ssi_exists, bic_format_valid, iban_format_valid, risk_limit_check [スタブ], compliance_check [スタブ]）
- `src/infrastructure/rule_engine.py` 新規
  - `run_fo_check(trade, db) → list[CheckResult]`
  - `run_bo_check(trade, db) → list[CheckResult]`
  - 結果を `trade.fo_check_results` / `trade.bo_check_results` に保存し、workflow_status を遷移
    - 全通過 → FoValidated / BoValidated
    - 失敗あり → FoAgentToCheck / BoAgentToCheck
- `src/presentation/routers/trades.py` 更新
  - `POST /api/v1/trades/{trade_id}/fo-check`: FoCheck 実行
  - `POST /api/v1/trades/{trade_id}/bo-check`: BoCheck 実行
- `src/presentation/routers/settings.py` 新規
  - `GET /api/v1/settings`: 設定一覧取得
  - `PATCH /api/v1/settings/{key}`: 設定値更新
- 自動トリガー実装: `fo_check_trigger=auto` の場合、`Initial` への遷移直後に FoCheck を自動実行。`bo_check_trigger=auto` の場合、`FoValidated` への遷移直後に BoCheck を自動実行。

---

## Backlog

### Phase 26 — FO/BO ワークフロー全面実装

> 取引の精算ライフサイクルを FO/BO 分離ワークフローで管理する。  
> ルールベース機械チェック → エージェントトリアージ → ユーザ承認 の 3 段構成により、  
> 人間が確認すべき案件を絞り込む。  
> 詳細設計は `docs/requirements.md` の Phase 26 セクションを参照。

---

#### Phase 26-A — DB Foundation + エンティティ拡張

**目的:** バージョン管理・ワークフローステータス・イベント・設定を支えるスキーマを追加する。

**Backend:**
- `src/domain/entities.py`
  - `TradeWorkflowStatus` enum 追加（11 値: Initial / FoCheck / FoAgentToCheck / FoUserToValidate / FoValidated / BoCheck / BoAgentToCheck / BoUserToValidate / BoValidated / Done / Cancelled / EventPending）
  - `EventType` enum 追加（AMEND / CANCEL）
  - `EventWorkflowStatus` enum 追加（FoUserToValidate / FoValidated / BoUserToValidate / BoValidated / Done / Cancelled）
  - `CheckResult` dataclass 追加（rule_name, passed, message）
  - `TradeEvent` entity 追加
- `src/infrastructure/db/models.py`
  - `TradeModel` を更新:
    - PK を UUID `id` に変更（現: `trade_id` が PK）
    - `(trade_id, version)` に UNIQUE 制約追加
    - カラム追加: `version INT DEFAULT 1`, `workflow_status VARCHAR(30)`, `is_current BOOL DEFAULT TRUE`
    - カラム追加: `sendback_count INT DEFAULT 0`, `fo_check_results JSONB`, `bo_check_results JSONB`
    - カラム追加: `bo_sendback_reason TEXT`, `fo_explanation TEXT`
  - `TradeEventModel` 新規追加（id, trade_id, from_version, to_version, event_type, workflow_status, requested_by, reason, amended_fields JSONB）
  - `AppSettingModel` 新規追加（key VARCHAR PK, value VARCHAR, description, updated_at）
- `alembic/versions/0003_add_workflow_schema.py` 作成
- `src/infrastructure/seed.py` 更新
  - STP_FAILED 取引（TRD-001〜005, TRD-008〜012）の `workflow_status` = `FoAgentToCheck`
  - NEW 取引（TRD-006〜007）の `workflow_status` = `Initial`
  - `app_settings` シードデータ: `fo_check_trigger=manual`, `bo_check_trigger=manual`
- `src/infrastructure/db/trade_repository.py` 更新
  - `get_current(trade_id)`: `is_current=True` の最新バージョンを返す
  - `list()`: `is_current=True` のみ返す（バージョン履歴は `list_versions(trade_id)` で取得）
  - `create_next_version(trade_id, event_type, amended_fields)`: バージョンインクリメント + EventPending 行追加
  - `activate_version(trade_id, version)`: `is_current` の切り替え
  - `update_workflow_status(trade_id, status, **kwargs)`: workflow_status + 付随フィールド更新
- `src/infrastructure/db/trade_event_repository.py` 新規
- `src/infrastructure/db/app_setting_repository.py` 新規

---

#### Phase 26-C — BoAgent リネーム + 拡張

**目的:** 既存エージェントを BoAgent として整理し、新しいワークフローに対応させる。

**Backend:**
- `src/infrastructure/agent.py` → `src/infrastructure/bo_agent.py` にリネーム
  - `build_graph()` → `build_bo_graph()`
  - `AgentState` → `BoAgentState`
  - `SYSTEM_PROMPT` → `BO_SYSTEM_PROMPT`
  - `_HITL_TOOL_TO_NODE` → `_BO_HITL_TOOL_TO_NODE`
- `src/infrastructure/triage_use_case.py` → `src/infrastructure/bo_triage_use_case.py` にリネーム
  - `TriageSTPFailureUseCase` → `BoTriageUseCase`
- `src/infrastructure/tools.py` 更新
  - `get_bo_check_results(trade_id)` 新規追加（read）
  - `get_fo_explanation(trade_id)` 新規追加（read）
  - `send_back_to_fo(trade_id, reason)` 新規追加（HITL write）
  - `escalate_to_bo_user(trade_id, reason)` 新規追加（write）
  - BoAgent のツールリスト・HITLリストを更新
- `BO_SYSTEM_PROMPT` 更新
  - BoCheck 結果を参照して調査する手順
  - 1 回目差し戻し: `send_back_to_fo` 呼び出し条件（FO 起因の問題）
  - 2 回目以降: `send_back_to_fo` 禁止、`escalate_to_bo_user` を使用
  - FoAgent の説明（`get_fo_explanation`）を考慮したトリアージ手順
- `src/presentation/routers/` 更新
  - `POST /api/v1/trades/{trade_id}/bo-triage` 新規追加
  - `POST /api/v1/trades/{trade_id}/bo-triage/{run_id}/resume` 新規追加
  - 既存 `/api/v1/stp-exceptions/{id}/start-triage` → BoTriage に委譲
- 全 import を `agent.py` → `bo_agent.py`、`TriageSTPFailureUseCase` → `BoTriageUseCase` に更新

---

#### Phase 26-D — FoAgent 新規実装

**目的:** FoCheck 結果を調査し、Amend/Cancel イベントの提案やBoAgent 差し戻し対応を行う FoAgent を実装する。

**Backend:**
- `src/infrastructure/tools.py` 更新
  - `get_fo_check_results(trade_id)` 新規追加（read）
  - `get_bo_sendback_reason(trade_id)` 新規追加（read）
  - `create_amend_event(trade_id, reason, amended_fields)` 新規追加（HITL write）
  - `create_cancel_event(trade_id, reason)` 新規追加（HITL write）
  - `provide_explanation(trade_id, explanation)` 新規追加（write: FoValidated に遷移）
  - `escalate_to_fo_user(trade_id, reason)` 新規追加（write: FoUserToValidate に遷移）
- `src/infrastructure/fo_agent.py` 新規
  - `FoAgentState` TypedDict
  - `FO_SYSTEM_PROMPT`: FoCheck 結果調査 → 修正提案/説明付与/エスカレーション
  - `_FO_HITL_TOOL_TO_NODE`: create_amend_event, create_cancel_event
  - `build_fo_graph()` → LangGraph StateGraph
- `src/infrastructure/fo_triage_use_case.py` 新規
  - `FoTriageUseCase`: start(trade_id) / resume(run_id, approved)
- `src/presentation/routers/trades.py` 更新
  - `POST /api/v1/trades/{trade_id}/fo-triage`
  - `POST /api/v1/trades/{trade_id}/fo-triage/{run_id}/resume`

---

#### Phase 26-E — トレードイベント API

**目的:** Amend/Cancel イベントの作成・承認・バージョン管理を API で操作できるようにする。

**Backend:**
- `src/presentation/routers/trade_events.py` 新規
  - `GET /api/v1/trades/{trade_id}/events`: イベント一覧（バージョン履歴含む）
  - `POST /api/v1/trades/{trade_id}/events`: イベント作成（FoUser から手動）
  - `PATCH /api/v1/trade-events/{event_id}/fo-approve`: FO 承認/却下
  - `PATCH /api/v1/trade-events/{event_id}/bo-approve`: BO 承認/却下
- バージョン管理ロジック（`trade_repository.py`）
  - イベント作成時: `create_next_version()` で EventPending 行生成
  - BO 承認完了時: `activate_version()` + 旧バージョン `is_current=False` 化
  - Amend Done: 新バージョン `workflow_status=Initial`（FoCheck から再スタート）
  - Cancel Done: 新バージョン `workflow_status=Cancelled`
- `src/presentation/schemas.py` 更新
  - `TradeEventOut`, `TradeEventCreateRequest`, `TradeVersionOut` 追加

---

#### Phase 26-F — フロントエンド

**目的:** 新しいワークフロー全体を UI で操作・確認できるようにする。

**Frontend:**
- `frontend/src/pages/TradeDetailPage.tsx` 新規（`/trades/:id`）
  - バージョン履歴タブ（バージョン一覧・各バージョンの workflow_status）
  - FoCheck/BoCheck 結果パネル（ルール名・pass/fail・メッセージ）
  - イベント一覧（Amend/Cancel）と FO/BO 承認ボタン
  - FoTriage / BoTriage 起動ボタン + HITL パネル（既存コンポーネント流用）
  - チェック実行ボタン（manual モード時のみ表示）
- `frontend/src/pages/SettingsPage.tsx` 新規（`/settings`）
  - FoCheck トリガー: auto / manual トグル
  - BoCheck トリガー: auto / manual トグル
- `frontend/src/pages/TradeListPage.tsx` 更新
  - `workflow_status` 列を追加
  - `workflow_status` フィルタ追加
  - バッジ色設計: FO系=青、BO系=緑、Done=グレー、Cancelled=赤、EventPending=オレンジ
  - 行クリックで TradeDetailPage に遷移
- `frontend/src/components/NavBar.tsx` 更新
  - `/settings` リンク追加
- `frontend/src/App.tsx` 更新
  - `/trades/:id` ルート追加
  - `/settings` ルート追加
- 新規 API クライアント: `src/api/tradeEvents.ts`, `src/api/settings.ts`
- 新規型定義: `src/types/tradeEvent.ts`, `src/types/settings.ts`



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

#### 24-A: ツールの追加 ✅ 完了

追加済みツール（tools.py / agent.py / triage_use_case.py）:
- `get_triage_history(trade_id)` — 同一取引の過去トリアージ結果（read-only）
- `get_counterparty_exception_history(lei)` — 直近30日の STP 失敗件数（3件以上で警告付き、read-only）
- `reactivate_counterparty(lei)` — `is_active=True` に更新（HITL承認対象）
- `update_ssi(lei, currency, ...)` — 既存 SSI の BIC/口座番号等を修正（HITL承認対象）
- `escalate(trade_id, reason)` — 担当者エスカレーション（HITL確認対象）

agent.py に `_HITL_TOOL_TO_NODE` dict と `_make_hitl_node` ファクトリを追加。
triage_use_case.py の HITL 判定を `register_ssi` ハードコードから汎化。

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

#### 24-C: アクション多様化（HITL の拡張）✅ 完了

追加済み HITL パターン（TriagePage.tsx の HitlPanel コンポーネント）:
- `register_ssi`: Approve Registration / Reject（オレンジ）
- `reactivate_counterparty`: Approve Reactivation / Reject + コンプライアンス警告（ブルー）
- `update_ssi`: Approve Update / Reject（パープル）
- `escalate`: Acknowledge & Escalate / Override（レッド + オペレーター警告）

Backend に `pending_action_type` フィールドを追加し、フロントエンドがアクション種別に応じた UI を表示。

#### 24-D: パターン分析 ✅ 完了

システムプロンプトに調査手順 3・4 を追加:
- ステップ 3: `get_counterparty_exception_history` — 30 日間に 3 件以上の失敗で警告を diagnosis に含める
- ステップ 4: `get_triage_history` — 同一 root_cause の解決済みトリアージがあれば "Previously resolved by: ..." を recommended_action に反映

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
- Phase 26-A: DB Foundation — TradeWorkflowStatus/EventType/CheckResult エンティティ追加、TradeModel PK→UUID + version/workflow_status/is_current 等カラム追加、TradeEventModel/AppSettingModel 新規、Alembic 0003 マイグレーション、seed.py 更新（workflow_status, app_settings）、trade_repository.py 拡張、trade_event_repository.py / app_setting_repository.py 新規
