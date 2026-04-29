# Task List

Task state = section position. No checkbox marks.
Transitions: Backlog → In Progress (before coding) → Done (after commit).
Max 1 task in In Progress at a time.

---

## In Progress

<!-- (empty) -->

---

## Done

- Phase 33: seed / rule_engine 整合性修正 — FO_RULES に counterparty_exists・instrument_exists stub 追加、BO_RULES に settlement_confirmed stub 追加、seed.py を静的チェック結果 pre-seed 方式に再設計（TRD-004/005 を FoAgentToCheck + fo_check_results、TRD-001〜003/008〜013 を BoAgentToCheck + fo/bo_check_results 付きで登録、_wf_status バグ修正）、Zenith Trading Corp（非アクティブ CP）の USD SSI をマスタに追加（TRD-009 が counterparty_active のみ失敗し AG01 パスになるよう調整）
- Phase 29: stp_status カラム削除 — TradeStatus enum 削除、models.py/trade_repository.py/seed.py/schemas.py/trades.py/stp_exceptions.py から stp_status 参照を全削除、alembic/versions/0005_drop_stp_status.py 追加、フロントエンド（types/api/TradeListPage/TradeDetailPage）から stp_status フィルタ・列・表示を削除、frontend version 0.2.1 → 0.3.0
- Phase 32: ハイブリッドエージェント デモ準備 — test_determine_triage_path.py（24テスト）、test_gather_context_routing.py（11テスト）、test_hybrid_routing.py（9テスト、全102件通過）、TRD-013 を mock_store.py + seed.py に追加（AM04 シナリオ、workflow_status=BoAgentToCheck + bo_check_results プリシード）、docs/demo_hybrid_agent.md（8シナリオのcurlデモ手順書）

---

#### Phase 32 — ハイブリッドエージェント デモ準備（テストシナリオ・シードデータ整備）

**目的:** Phase 31 で実装したハイブリッド構造（決定論的 + 自律的パス）を実証・検証するためのテストシナリオ、シードデータ、テストコードを整備する。

---

##### テストシナリオ一覧（8 件）

| # | Trade ID | トリガー条件 | 期待 triage_path | 期待アクション | パス種別 |
|---|----------|------------|----------------|--------------|---------|
| 1 | TRD-009 | `AG01` in error_message | `AG01` | `reactivate_counterparty` (HITL) | 決定論的 |
| 2 | TRD-001 | `ssi_exists` 失敗、外部 SSI あり | `MISSING_SSI` | `register_ssi` (HITL) | 決定論的 |
| 3 | TRD-008 | `AC01` in error_message、外部 SSI なし | `MISSING_SSI` | `escalate_to_bo_user` (直接) | 決定論的 |
| 4 | TRD-011 | `iban_format_valid` 失敗 または `BE01` | `BE01` | `escalate_to_bo_user` (直接) | 決定論的 |
| 5 | TRD-013 (新規) | `AM04` in error_message、sendback_count=0 | `AM04` | `send_back_to_fo` (HITL) | 決定論的 |
| 6 | TRD-013 (sendback 状態) | `AM04` in error_message、sendback_count≥1 | `AM04` | `escalate_to_bo_user` (直接) | 決定論的 |
| 7 | TRD-010 | `counterparty_active` + `ssi_exists` 失敗 | `COMPOUND` | `deep_investigation_node`（自律 ReAct） | 自律的 |
| 8 | TRD-012 | 不明エラー・ルール失敗なし | `UNKNOWN` | `deep_investigation_node`（自律 ReAct） | 自律的 |

各シナリオで確認すべきこと：
- `state["triage_path"]` が期待値と一致しているか
- `snapshot.next[0]` が期待するノード名（HITL ノードまたは `deep_investigation`）か
- 決定論的パスでは LLM 呼び出しが summary の 1 回のみか（`cost_log` で確認）
- `action_taken=True` が適切なタイミングで set されているか

---

##### 必要な実装・ツール

**1. `tests/unit/test_determine_triage_path.py`（新規）**

`_determine_triage_path()` 純粋関数の単体テスト。DB・LLM 不要。

```python
# カバーすべきケース
("AG01 in error_message", "AG01", [], "AG01"),
("counterparty_active in failed_rules", "", ["counterparty_active"], "AG01"),
("BE01 in error_message", "BE01 mismatch", [], "BE01"),
("bic_format_valid failed", "", ["bic_format_valid"], "BE01"),
("iban_format_valid failed", "", ["iban_format_valid"], "BE01"),
("AM04 in error_message", "AM04 liquidity", [], "AM04"),
("AC01 in error_message", "AC01 account", [], "MISSING_SSI"),
("ssi_exists failed", "", ["ssi_exists"], "MISSING_SSI"),
("複数ルール失敗 → COMPOUND", "", ["counterparty_active", "ssi_exists"], "COMPOUND"),
("AG01 + BE01 同時 → COMPOUND", "AG01 BE01", [], "COMPOUND"),
("何も該当しない → UNKNOWN", "Generic error", [], "UNKNOWN"),
```

**2. `tests/unit/test_gather_context_routing.py`（新規）**

`gather_context_node` の単体テスト：`get_bo_check_results` / `get_trade_detail` をモックして `triage_path` / `sendback_count` / `failed_rules` の state 更新を検証。LangGraph の `MemorySaver` で軽量グラフを組んで実行可能。LLM 呼び出しなし。

```python
# モック戦略：tools.py の関数を unittest.mock.patch で差し替える
# patch("src.infrastructure.bo_agent.get_bo_check_results", return_value=json.dumps({...}))
# 検証：returned_dict["triage_path"] == "AG01"
```

**3. `tests/integration/test_hybrid_routing.py`（新規）**

決定論的パスのみを対象にした統合テスト（`@pytest.mark.integration`）。DB 必要・LLM 不要。

```python
# 手順：
# 1. 対象 trade の bo_check_results を DB に手動 set
# 2. graph.invoke(initial_state, config) を呼び出す
# 3. snapshot.next[0] が期待するノード名か検証（interrupt_before で停止する）
# 4. cost_log に LLM 呼び出しが含まれないことを確認（決定論的パス）
```

対象シナリオ：#1（AG01）、#3（MISSING_SSI+escalate）、#4（BE01）、#5（AM04+sendback0）

**4. `src/infrastructure/seed.py` 更新**

- **TRD-013 追加（AM04 シナリオ）:** counterparty・SSI は正常だが FO 側の流動性問題を想定。error_message に `"AM04"` を含む。workflow_status = `BoAgentToCheck`
- **TRD-008〜012 の `bo_check_results` を手動シード:** 各 trade の真の原因に対応したルール失敗リストを `bo_check_results` カラムに INSERT する（rule_engine の `run_bo_check` を seed 時に呼び出すか、JSON を直接 set）

```python
# 例：TRD-011 の bo_check_results シード
# [{"rule_name": "iban_format_valid", "passed": False, "severity": "error",
#   "message": "IBAN GB29NWBK... is not valid for currency GBP"}]
```

**5. `src/infrastructure/mock_store.py` 更新**

- TRD-013 用のモックトレードデータ追加（`_TRADES` dict）
- TRD-011 用の外部 SSI エントリなし確認（IBAN エラーの場合、外部 SSI も同様に無効なので意図的に登録しない）
- TRD-009 (AG01) の外部 SSI エントリ不在を確認（counterparty 再アクティブ化後に SSI を別途確認するフローのため）

**6. デモ実行手順書**

`docs/demo_hybrid_agent.md`（新規、markdown）

```
シナリオ別の curl コマンド例と期待される triage_path / 実際の HITL 停止ノード一覧。
cost_log を比較して決定論的パス（LLM 1 回）vs 自律パス（LLM 複数回）のコスト差を示す。
```

---

##### 検証コマンド

```bash
# LLM・DB 不要（即時実行可能）
uv run pytest tests/unit/test_determine_triage_path.py -v
uv run pytest tests/unit/test_gather_context_routing.py -v

# DB 必要・LLM 不要（決定論的パスのみ）
uv run pytest tests/integration/test_hybrid_routing.py -m integration -v

# フル統合テスト（ANTHROPIC_API_KEY 必要）
uv run pytest tests/integration/ -m integration -v
```

---

## Backlog

#### Phase 28 — 取引入力画面：Counterparty 検索モーダル

**目的:** 取引入力フォームの Counterparty 選択をプルダウンからモーダル検索に変更する。
現状はプルダウンに全件ロードしているため、件数が増えると使いにくい。

**Frontend:**
- `frontend/src/pages/TradeInputPage.tsx` 更新
  - Counterparty フィールドを `<select>` から「選択済み表示 + 変更ボタン」に変更
  - ボタン押下でモーダルを開く
  - モーダル内: 名前前方一致・LEI 部分一致などで検索 → 結果一覧から1件選択
  - 選択後モーダルを閉じ、フォームに LEI + 名前を反映
- API: `GET /api/v1/counterparties?name=<prefix>&lei=<partial>` を活用（既存エンドポイント）

---

#### Phase 26-F — フロントエンド ✅ 完了

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

- Phase 31: BO/FO エージェント ハイブリッド構造リファクタリング — gather_context_node（決定論的データ収集）、AG01/BE01/AM04/MISSING_SSI 別ハンドラノード、HITL ノード二重登録（決定論的パス用 + deep_investigation 用）、_determine_triage_path 純粋関数、BO_SYSTEM_PROMPT / FO_SYSTEM_PROMPT から INVESTIGATION STEPS 削除（~40 行削減）、bo_triage_use_case.py の _BO_ALL_HITL_NODE_NAMES 対応 + resume() as_node 修正
- Phase 30: コスト計測・モデル選択機能 — utils/cost_tracker.py（価格テーブル/calc_cost/build_cost_log/select_model/call_with_cost_tracking）、FoAgentState/BoAgentState に cost_log・total_cost_usd・task_type・selected_model 追加、model_router_node を fo/bo_agent 先頭に挿入（task_type と $0.10 閾値でモデル選択 + 監査ログ）、agent_node を call_with_cost_tracking() でラップ、use_case initial_state 更新、test_cost_tracker.py 追加（24テスト、計58件通過）
- Phase 27: 取引入力機能 + maybe_run_fo_check チェーン修正 — TradeCreateRequest スキーマ追加、POST /api/v1/trades エンドポイント追加、maybe_run_fo_check が FoValidated 時に maybe_run_bo_check を自動チェーン、fo-check エンドポイントも同様に修正、TradeInputPage（日付カレンダー + マスタデータ選択）、TradeListPage に "New Trade" ボタン、フロントエンドバージョン 0.1.8 → 0.2.0
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
- Phase 26-B: ルールエンジン — CheckResult に severity 追加、check_rules.py（FoRule/BoRule + FoCheck 7 ルール + BoCheck 7 ルール）、rule_engine.py（run_fo_check/run_bo_check/maybe_* auto-trigger）、POST /api/v1/trades/{id}/fo-check・bo-check エンドポイント、settings.py ルーター（GET /api/v1/settings + PATCH /api/v1/settings/{key}）
- Phase 26-C: BoAgent リネーム + 拡張 — tools.py に get_bo_check_results/get_fo_explanation/send_back_to_fo/escalate_to_bo_user 追加、bo_agent.py（BoAgentState + build_bo_graph() + 4 HITL ノード + BO_SYSTEM_PROMPT）、bo_triage_use_case.py（BoTriageUseCase）、routers/bo_triage.py（POST /api/v1/trades/{id}/bo-triage + resume）、test_entities.py の RootCause 期待値更新
- Phase 26-D: FoAgent 新規実装 — tools.py に get_fo_check_results/get_bo_sendback_reason/create_amend_event/create_cancel_event/provide_explanation/escalate_to_fo_user 追加 + FO_*_TOOLS エクスポート、fo_agent.py（FoAgentState + build_fo_graph() + 2 HITL ノード + FO_SYSTEM_PROMPT）、fo_triage_use_case.py（FoTriageUseCase）、routers/fo_triage.py（POST /api/v1/trades/{id}/fo-triage + resume）
- Phase 26-E: トレードイベント API — schemas.py に TradeVersionOut/TradeEventOut/TradeEventListResponse/TradeEventCreateRequest/EventApproveRequest 追加、routers/trade_events.py（GET list / POST create / PATCH fo-approve / PATCH bo-approve、状態機械: FoUserToValidate→FoValidated→Done、AMEND承認で activate_version()+Initial 遷移、CANCEL承認で Cancelled 遷移）
- Phase 26-F: フロントエンド — TradeOut に check results 追加、TradeDetailPage（4タブ: FoCheck/BoCheck/Events/Triage）、SettingsPage、TradeListPage 更新（workflow_status列/フィルタ/クリックナビ）、NavBar+App.tsx 更新
