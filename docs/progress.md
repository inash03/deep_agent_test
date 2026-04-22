# Progress Log

---

## Current Status

**Branch:** `claude/update-documentation-PRK0f`
**Last updated:** 2026-04-22
**In Progress:** —
**Next:** 次フェーズ（Phase 28 Counterparty 検索モーダル or Phase 29 stp_status 削除）の着手

---

## Step Log

### Step 36 — docs: README / architecture / requirements / Skills.md を Phase 26-27 に同期 (2026-04-22)

Files: `README.md`, `docs/architecture.md`, `docs/requirements.md`, `docs/Skills.md`, `docs/tasks.md`

- **README.md**: FoAgent/BoAgent をアーキテクチャ概要に追記。API リファレンスに取引作成・FoCheck/BoCheck・FO/BO トリアージ・トレードイベント・設定の各エンドポイントを追加。HITL フローセクションに FoAgent（2 アクション）と BoAgent（4 アクション）の HITL フローを追加。プロジェクト構成に新ファイル（fo_agent.py 等）・新フロントエンドページ（TradeDetailPage 等）・新マイグレーション（0003/0004）を追加
- **docs/architecture.md**: エージェント構成表を追加（Legacy/FoAgent/BoAgent）。FoAgent（2 HITL ノード）/ BoAgent（4 HITL ノード）の StateGraph Mermaid 図を追加。Clean Architecture 図を更新（新ルーター・新インフラ・DB リポジトリ）。DB ER 図を更新（trades UUID PK/workflow 拡張、trade_events/app_settings 追加）。ツール一覧を3エージェント別テーブルに分割。フロントエンド画面一覧に TradeInputPage/TradeDetailPage/SettingsPage を追加
- **docs/requirements.md**: Phase 26 の FR-15〜FR-25 を実装済みセクションに移動（`Done` に変更）。Phase 27 の FR-26/FR-27 を追加。セクションタイトルを「Phase 1〜27」に更新
- **docs/Skills.md**: 新規作成 — `update-docs` スキルを定義（ストリームタイムアウト回避のための並列エージェントパターン）

**タイムアウト対策:** 大ファイルの一括更新によるストリームアイドルタイムアウトを回避するため、3 ファイルを独立したサブエージェントに並列委譲するパターンを採用・文書化

---

### Step 35 — feat: 取引入力機能 + FoCheck→BoCheck 自動チェーン修正 (2026-04-19)

Files: `src/presentation/schemas.py`, `src/presentation/routers/trades.py`,
       `src/infrastructure/rule_engine.py`,
       `frontend/src/api/trades.ts`, `frontend/src/pages/TradeInputPage.tsx`,
       `frontend/src/pages/TradeListPage.tsx`, `frontend/src/App.tsx`,
       `frontend/src/version.ts`, `docs/tasks.md`

- **schemas.py**: `TradeCreateRequest` スキーマ追加（trade_id, trade_date, value_date, counterparty_lei, instrument_id, currency, amount）
- **trades.py**: `POST /api/v1/trades` エンドポイント追加 — 取引作成後に `maybe_run_fo_check` を自動実行。`POST /{id}/fo-check` が FoValidated を返した場合に `maybe_run_bo_check` を自動チェーン
- **rule_engine.py**: `maybe_run_fo_check` が auto モードで FoValidated になった場合、`maybe_run_bo_check` を続けて呼び出すよう修正（定義されていたが呼び出し元がなかった問題を解消）
- **TradeInputPage.tsx**: 新規フォームページ — TradeDate/ValueDate は `<input type="date">` カレンダー、Counterparty/Instrument はマスタデータから取得したドロップダウン、Currency は選択 Instrument の ID（6文字）から前後3文字を派生、Amount は数値入力。作成成功後は取引詳細ページへ遷移
- **TradeListPage.tsx**: "New Trade" ボタンを PageLayout action に追加（`/trades/new` へ遷移）
- **App.tsx**: `/trades/new` ルートを `/trades/:trade_id` より前に登録（ルートシャドウ防止）
- **version.ts**: `0.1.8 → 0.2.0`

---

### Step 34 — Fix: FoCheck 自動実行 + 初期ステータス修正 (2026-04-19)

Files: `src/infrastructure/seed.py`, `src/infrastructure/rule_engine.py`,
       `src/presentation/routers/trade_events.py`,
       `alembic/versions/0004_fix_focheck_initial_status.py`

- **seed.py**: STP_FAILED 取引（TRD-001〜005, TRD-008〜012）の初期 `workflow_status` を `FoAgentToCheck` → `FoCheck` に修正（FoCheck 未実行なのに `FoAgentToCheck` になっていた誤りを解消）。`_maybe_auto_run_fo_check()` ヘルパーを追加し `seed_database()` / `reset_and_seed()` の末尾で呼び出す。`fo_check_trigger=auto` の場合は全 `FoCheck` 取引に対して即時 `run_fo_check()` を実行
- **rule_engine.py**: `maybe_run_fo_check` を拡張 — auto モードは従来通り `run_fo_check()` を実行。manual モードは `workflow_status='FoCheck'` をセットして commit（`Initial` → `FoCheck` への遷移を担当）。`maybe_run_bo_check` も同様に `BoCheck` をセット
- **trade_events.py**: `bo_approve_event` の AMEND 承認後に `maybe_run_fo_check(trade_id, db)` を呼び出す。auto → 即 FoCheck 実行、manual → `FoCheck` ステータスにセット。失敗しても本体の event 応答には影響させない（ログ警告のみ）
- **alembic/versions/0004**: 既存 DB の `workflow_status='FoAgentToCheck' AND fo_check_results IS NULL` の行を `FoCheck` に修正するマイグレーションを追加

---

### Step 33 — Fix: ロギング KeyError + STP Exception 画面再設計 (2026-04-19)

Files: `src/infrastructure/fo_agent.py`, `src/infrastructure/bo_agent.py`, `src/infrastructure/agent.py`,
       `frontend/src/pages/StpExceptionListPage.tsx`, `frontend/src/version.ts`

- ロギング: `_make_hitl_node` の `extra={"args": ...}` を `"tool_args"` にリネーム（Python LogRecord の予約キー衝突を修正）
- STP Exception 画面: "Error Message" 列を削除（旧 STP エラーテキストで FO/BO ルール違反とは別物）
- 旧 "Triage" ボタンを削除（旧 `TriageUseCase`/`agent.py` を呼ぶ旧来 API — 新 FO/BO トリアージとは無関係）
- "View Violations" ボタン追加 → モーダルが `GET /api/v1/trades/{id}` を取得し、FO/BO 各チェックの失敗ルールを全件表示
- "Open Trade" ボタン追加 → 取引詳細ページ（FO/BO トリアージ実行場所）へ遷移
- フロントエンドバージョン `0.1.5 → 0.1.6`

---

### Step 32 — Fix: /resume 500 エラー（CORSヘッダー欠落・型ミスマッチ） (2026-04-19)

Files: `src/main.py`, `src/infrastructure/tools.py`,
       `src/infrastructure/fo_agent.py`, `src/infrastructure/bo_agent.py`,
       `frontend/src/version.ts`

- `main.py`: グローバル例外ハンドラ追加 — FastAPI の CORSMiddleware はハンドルされない 500 例外のレスポンスに CORS ヘッダーを付与しないため、`@app.exception_handler(Exception)` で手動付与する
- `tools.py`: `create_amend_event` の `amended_fields` が LLM から dict で渡された場合に `TypeError` が発生していた → `isinstance(amended_fields, dict)` チェックを追加し、`JSONDecodeError` と `TypeError` の両方を捕捉
- `fo_agent.py` / `bo_agent.py`: `_make_hitl_node` の `tool_fn.invoke()` を try/except で囲み、ツール実行エラーをグラフクラッシュではなく `ToolMessage(success=False)` として返すよう修正
- フロントエンドバージョン `0.1.4 → 0.1.5`（パッチバンプ）

### Step 31 — Fix: unused useNavigate import (TS6133) (2026-04-19)

Files: `frontend/src/components/NavBar.tsx`, `frontend/src/version.ts`

- Removed unused `useNavigate` import from `NavBar.tsx` that caused CI `error TS6133`
- Bumped version `0.1.0 → 0.1.1` (patch: bug fix)

---

### Step 30 — Phase 26-F: フロントエンド (2026-04-18)

Files: `src/presentation/schemas.py`, `src/presentation/routers/trades.py`,
       `frontend/src/types/trade.ts` (更新), `frontend/src/types/tradeEvent.ts` (新規),
       `frontend/src/types/settings.ts` (新規),
       `frontend/src/api/trades.ts` (更新), `frontend/src/api/tradeEvents.ts` (新規),
       `frontend/src/api/settings.ts` (新規),
       `frontend/src/pages/SettingsPage.tsx` (新規),
       `frontend/src/pages/TradeDetailPage.tsx` (新規),
       `frontend/src/pages/TradeListPage.tsx` (更新),
       `frontend/src/components/NavBar.tsx` (更新), `frontend/src/App.tsx` (更新)

- `schemas.py` / `trades.py`: `TradeOut` に `fo_check_results`・`bo_check_results`（list[dict]|None）追加、`_to_out()` で返却
- `types/trade.ts`: `CheckResult`・`CheckResultsResponse` 追加。`Trade` に `version`/`workflow_status`/`is_current`/check results 追加。`WORKFLOW_STATUS_LABELS`・`WORKFLOW_STATUS_COLORS`（12値）追加
- `types/tradeEvent.ts`: `TradeEvent`・`EVENT_STATUS_LABELS`/`COLORS` 定義（新規）
- `types/settings.ts`: `AppSetting` 定義（新規）
- `api/trades.ts`: `workflow_status` パラメータ追加。`runFoCheck`/`runBoCheck`/`startFoTriage`/`resumeFoTriage`/`startBoTriage`/`resumeBoTriage` 追加
- `api/tradeEvents.ts`: `listTradeEvents`/`createTradeEvent`/`foApproveEvent`/`boApproveEvent`（新規）
- `api/settings.ts`: `listSettings`/`updateSetting`（新規）
- `pages/SettingsPage.tsx`: fo/bo_check_trigger auto/manual トグル UI（新規）
- `pages/TradeDetailPage.tsx`: 4 タブ（FoCheck・BoCheck・Events・Triage）。FoCheck/BoCheck 結果テーブル + Run ボタン、Events 一覧 + 作成フォーム + FO/BO 承認ボタン、FO/BO Triage HITL パネル（新規）
- `pages/TradeListPage.tsx`: workflow_status 列・フィルタ追加、行クリック → TradeDetailPage 遷移
- `NavBar.tsx`: Settings リンク追加
- `App.tsx`: `/trades/:trade_id` + `/settings` ルート追加
- TypeScript エラーなし、バックエンド 34 テスト通過

### Step 29 — Phase 26-E: トレードイベント API (2026-04-18)

Files: `src/presentation/schemas.py`, `src/presentation/routers/trade_events.py` (新規),
       `src/main.py`

- `schemas.py`: `TradeVersionOut`（バージョン詳細）、`TradeEventOut`（イベント詳細）、`TradeEventListResponse`、`TradeEventCreateRequest`（event_type/reason/requested_by/amended_fields）、`EventApproveRequest`（approved/comment）を追加
- `routers/trade_events.py`:
  - `GET /api/v1/trades/{trade_id}/events` — TradeEventRepository.list_for_trade() 返却
  - `POST /api/v1/trades/{trade_id}/events` — AMEND: create_next_version() + trade EventPending 遷移 + TradeEvent 作成。CANCEL: TradeEvent のみ作成。重複イベントは 409 で弾く
  - `PATCH /api/v1/trade-events/{id}/fo-approve` — 承認: FoValidated 遷移。却下: Cancelled + AMEND の場合は pending version を削除し trade を FoAgentToCheck に戻す
  - `PATCH /api/v1/trade-events/{id}/bo-approve` — 承認+AMEND: activate_version() + 新バージョン workflow_status=Initial（FoCheck 再スタート）。承認+CANCEL: trade workflow_status=Cancelled。却下: Cancelled + pending version 削除
- `main.py`: `trade_events_router` を登録
- 全 34 ユニットテスト通過

### Step 28 — Phase 26-D: FoAgent 新規実装 (2026-04-18)

Files: `src/infrastructure/tools.py`, `src/infrastructure/fo_agent.py` (新規),
       `src/infrastructure/fo_triage_use_case.py` (新規),
       `src/presentation/routers/fo_triage.py` (新規), `src/main.py`

- `tools.py`: `get_fo_check_results(trade_id)` — fo_check_results JSONB + workflow_status + sendback_count 返却。`get_bo_sendback_reason(trade_id)` — bo_sendback_reason フィールド取得。`create_amend_event(trade_id, reason, amended_fields)` — HITL: create_next_version() + 現バージョン EventPending 遷移。`create_cancel_event(trade_id, reason)` — HITL: Cancelled 遷移。`provide_explanation(trade_id, explanation)` — 非HITL: FoValidated 遷移 + fo_explanation 保存。`escalate_to_fo_user(trade_id, reason)` — 非HITL: FoUserToValidate 遷移。`FO_READ_ONLY_TOOLS`（7ツール）・`FO_HITL_TOOLS`（2ツール）・`FO_ALL_TOOLS`（9ツール）エクスポート追加
- `fo_agent.py`: `_FO_HITL_TOOL_TO_NODE`（create_amend_event/create_cancel_event → 各 node）。`FoAgentState` TypedDict。`FO_SYSTEM_PROMPT`（調査手順4ステップ + 是正アクション A〜D）。`build_fo_graph()` — 2 HITL ノード + read_tools_node + agent_node、`interrupt_before=["create_amend_event_node", "create_cancel_event_node"]`
- `fo_triage_use_case.py`: `FoTriageUseCase.start(trade_id, error_context)` / `.resume(run_id, approved)` — bo_triage_use_case.py と同構造、FO グラフ用に実装
- `routers/fo_triage.py`: `POST /api/v1/trades/{trade_id}/fo-triage` + `POST /api/v1/trades/{trade_id}/fo-triage/{run_id}/resume`
- `main.py`: `fo_triage_router` を登録
- 全 34 ユニットテスト通過

### Step 27 — Phase 26-C: BoAgent リネーム + 拡張 (2026-04-18)

Files: `src/infrastructure/tools.py`, `src/infrastructure/bo_agent.py` (新規),
       `src/infrastructure/bo_triage_use_case.py` (新規),
       `src/presentation/routers/bo_triage.py` (新規), `src/main.py`,
       `tests/unit/test_entities.py`

- `tools.py`: `get_bo_check_results(trade_id)` — JSONB + sendback_count + workflow_status 返却。`get_fo_explanation(trade_id)` — FoAgent の説明取得。`send_back_to_fo(trade_id, reason)` — HITL: FoAgentToCheck 遷移 + sendback_count インクリメント + bo_sendback_reason 保存。`escalate_to_bo_user(trade_id, reason)` — 非HITL: BoUserToValidate 遷移。`BO_READ_ONLY_TOOLS`・`BO_HITL_TOOLS`・`BO_ALL_TOOLS` エクスポート追加
- `bo_agent.py`: `_BO_HITL_TOOL_TO_NODE`（register_ssi/reactivate_counterparty/update_ssi/send_back_to_fo → 各 node）。`BoAgentState` TypedDict。`BO_SYSTEM_PROMPT`（調査手順5ステップ + 是正アクション A〜E + sendback_count ガード + SWIFT コード）。`build_bo_graph()` — 4 HITL ノード + read_tools_node + agent_node、`interrupt_before=hitl_node_names`
- `bo_triage_use_case.py`: `BoTriageUseCase.start(trade_id, error_context)` / `.resume(run_id, approved)` — triage_use_case.py と同構造、BO グラフ用に移植
- `routers/bo_triage.py`: `POST /api/v1/trades/{trade_id}/bo-triage` + `POST /api/v1/trades/{trade_id}/bo-triage/{run_id}/resume`
- `main.py`: `bo_triage_router` を登録
- `test_entities.py`: `RootCause` 期待値に IBAN_FORMAT_ERROR / SWIFT_AC01 / SWIFT_AG01 / COMPOUND_FAILURE を追加（全 34 ユニットテスト通過）

### Step 26 — Phase 26-B: ルールエンジン実装 (2026-04-18)

Files: `src/domain/entities.py` (severity追加), `src/domain/check_rules.py` (新規),
       `src/infrastructure/rule_engine.py` (新規),
       `src/presentation/schemas.py`, `src/presentation/routers/trades.py`,
       `src/presentation/routers/settings.py` (新規), `src/main.py`

- `entities.py`: `CheckResult` に `severity: str = "error"` フィールド追加
- `check_rules.py`: `FoRule`・`BoRule` dataclass 定義。FoCheck 7 ルール実装（trade_date_not_future/not_weekend, value_date_after_trade_date/not_past/settlement_cycle[警告], amount_positive, settlement_currency_consistency）。BoCheck 7 ルール実装（counterparty_exists/active, ssi_exists, bic_format_valid, iban_format_valid, risk_limit_check[スタブ], compliance_check[スタブ]）
- `rule_engine.py`: `run_fo_check(trade_id, db)` — ERROR 失敗あり→FoAgentToCheck / なし→FoValidated。`run_bo_check(trade_id, db)` — 失敗あり→BoAgentToCheck / なし→BoValidated。`maybe_run_fo_check`・`maybe_run_bo_check` — app_settings の auto/manual を参照する auto-trigger ヘルパー
- `trades.py` ルーター: `POST /api/v1/trades/{id}/fo-check`・`POST /api/v1/trades/{id}/bo-check` エンドポイント追加（CheckResultsResponse 返却）
- `settings.py` ルーター（新規）: `GET /api/v1/settings` + `PATCH /api/v1/settings/{key}`
- `main.py`: settings_router を登録

### Step 25 — Phase 26-A: DB Foundation + エンティティ拡張 (2026-04-18)

Files: `src/domain/entities.py`, `src/infrastructure/db/models.py`,
       `alembic/versions/0003_add_workflow_schema.py`,
       `src/infrastructure/seed.py`,
       `src/infrastructure/db/trade_repository.py`,
       `src/infrastructure/db/trade_event_repository.py` (新規),
       `src/infrastructure/db/app_setting_repository.py` (新規),
       `src/presentation/schemas.py`, `src/presentation/routers/trades.py`

- `entities.py`: `TradeWorkflowStatus`（12値）、`EventType`（AMEND/CANCEL）、`EventWorkflowStatus`（6値）、`CheckResult`、`TradeEvent` を追加
- `models.py`: `TradeModel` の PK を UUID `id` に変更、`(trade_id, version)` UNIQUE 追加、`workflow_status`/`version`/`is_current`/`sendback_count`/`fo_check_results`/`bo_check_results`/`bo_sendback_reason`/`fo_explanation` カラム追加。`TradeEventModel`・`AppSettingModel` 新規追加
- Alembic 0003: 既存行への `gen_random_uuid()` 付与、STP_FAILED → `FoAgentToCheck` 一括更新、`trade_events`・`app_settings` テーブル作成、デフォルト設定（fo/bo_check_trigger=manual）挿入
- `seed.py`: 全 Trade にv`ersion=1`/`is_current=True`/`workflow_status` を付与、`AppSettingModel` の upsert 追加
- `trade_repository.py`: `list()` に `is_current=True` フィルタ追加、`get_current()`・`list_versions()`・`create_next_version()`・`activate_version()`・`update_workflow_status()` 追加
- `schemas.py`/`routers/trades.py`: `TradeOut` に `version`/`workflow_status`/`is_current` 追加、`workflow_status` フィルタパラメータ追加

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
