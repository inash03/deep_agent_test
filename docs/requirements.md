# Requirements

---

## Project Overview

**Name:** deep_agent_test
**Purpose:** LangGraph の ReAct エージェントを使い、証券会社のホールセール業務（STP失敗トレードの原因診断・修正）を自動化するサンプルプロジェクト。フロント/バックオフィスの承認ワークフロー全体を通じて、LangGraph の主要コンセプト（StateGraph, HITL, multi-agent）を実践的に理解することを目標とする。

---

## Goals

1. LangGraph の `StateGraph` + ReAct パターンでエージェントを構築・実行できる
2. LLM が動的にツールを選択する Multi-step reasoning の動作を理解する
3. `interrupt_before` / HITL を実装・拡張できる
4. Clean Architecture に従った Python バックエンド構成を実践する
5. **FoAgent / BoAgent の分割による、役割ベースのマルチエージェント設計を理解する**
6. **ルールベースの機械チェックとエージェントトリアージの組み合わせによって、人間の確認作業を削減するコンセプトを具現化する**

---

## Domain Model

### 取引ライフサイクル（WorkflowStatus）

取引は以下のステータスを順に遷移する。機械チェック（FoCheck/BoCheck）が全通過した場合はエージェントトリアージをスキップする。

| ステータス | 説明 | 担当 |
|-----------|------|------|
| `Initial` | 取引登録直後 | システム |
| `FoCheck` | フロントオフィス ルールチェック実行中 | システム |
| `FoAgentToCheck` | FoCheck 失敗あり → FoAgent がトリアージ | FoAgent |
| `FoUserToValidate` | FoAgent が人間判断が必要と判定 | FoUser |
| `FoValidated` | FO 承認完了 | システム |
| `BoCheck` | バックオフィス ルールチェック実行中 | システム |
| `BoAgentToCheck` | BoCheck 失敗あり → BoAgent がトリアージ | BoAgent |
| `BoUserToValidate` | BoAgent が人間判断が必要と判定 | BoUser |
| `BoValidated` | BO 承認完了 → 精算システムへ送出 | システム |
| `Done` | 全承認完了 | システム |
| `Cancelled` | Cancel イベントが承認され取引が取り消された | システム |
| `EventPending` | イベント（Amend/Cancel）承認待ち中の新バージョン | システム |

**遷移図:**

```
Initial
  → FoCheck (自動 or 手動トリガー)
    → [全通過] FoValidated
    → [失敗あり] FoAgentToCheck
        → [エージェント解決] FoValidated
        → [人間必要] FoUserToValidate → FoValidated
  → BoCheck (自動 or 手動トリガー)
    → [全通過] BoValidated → Done
    → [失敗あり] BoAgentToCheck
        → [エージェント解決] BoValidated → Done
        → [差し戻し 1回目] FoAgentToCheck (BoAgent の理由付き)
            → FoAgent が説明付きで FoValidated
                → BoCheck 再実行 → BoAgentToCheck (2回目)
                    → [解決] BoValidated → Done
                    → [2回目も問題あり] BoUserToValidate → BoValidated → Done
        → [解決不能] BoUserToValidate → BoValidated → Done
  Cancelイベント Done → Cancelled
```

### 取引バージョン管理

- 取引は `trade_id` + `version` で識別される
- 初回記帳: `version=1`
- イベント（Amend/Cancel）が発生するたびに `version` をインクリメント
- 新バージョン取引は承認完了まで `EventPending` 状態（無効）
- 承認完了後: 新バージョンが有効化、旧バージョンは履歴として保持
- `is_current=True` のレコードが現在の有効バージョン

```
trade_id=TRD-001, version=1, workflow_status=FoValidated, is_current=True
  └─ Amendイベント発生
       trade_id=TRD-001, version=2, workflow_status=EventPending, is_current=False
       └─ イベント承認完了 (Done)
            trade_id=TRD-001, version=2, workflow_status=Initial, is_current=True
            trade_id=TRD-001, version=1, is_current=False (履歴)
```

### トレードイベント（Amend / Cancel）

| 項目 | 内容 |
|------|------|
| **種別** | `AMEND`（修正）, `CANCEL`（取り消し） |
| **作成者** | FoUser または FoAgent (HITL承認必須) |
| **同時複数** | 不可（1取引に対し1イベントのみ進行中可能）|
| **ワークフロー** | FoUserToValidate → FoValidated → BoUserToValidate → BoValidated → Done |
| **Amend Done** | 新バージョン取引が `Initial` から再スタート |
| **Cancel Done** | 新バージョン取引が `Cancelled` に遷移 |

> **設計メモ (将来対応):** 複数イベント同時進行が必要になった場合は、進行中イベントをキャンセルした後に新しいイベントを起票する運用を想定。本プロジェクトでは未実装。

---

## Rule-Based Checks

### FoCheck ルール（取引内容の整合性）

| ルール名 | 内容 | 失敗時の扱い |
|---------|------|------------|
| `trade_date_not_future` | 約定日が未来でない | エラー |
| `trade_date_not_weekend` | 約定日が平日 | エラー |
| `value_date_after_trade_date` | 決済日 > 約定日 | エラー |
| `value_date_not_past` | 決済日が過去でない | エラー |
| `value_date_settlement_cycle` | 決済日が T+2 以降（FX 標準） | 警告 |
| `amount_positive` | 金額 > 0 | エラー |
| `settlement_currency_consistency` | 決済通貨が銘柄の通貨と整合 | エラー |

### BoCheck ルール（マスタ・リスク・コンプライアンス）

| ルール名 | 内容 | 失敗時の扱い |
|---------|------|------------|
| `counterparty_exists` | 取引先 LEI がマスタに存在 | エラー |
| `counterparty_active` | 取引先 `is_active=True` | エラー |
| `ssi_exists` | LEI/通貨の SSI が登録済み | エラー |
| `bic_format_valid` | BIC が 8 または 11 文字 | エラー |
| `iban_format_valid` | IBAN が有効形式（存在する場合） | エラー |
| `risk_limit_check` | 与信枠チェック **（スタブ: 常に通過）** | エラー |
| `compliance_check` | コンプライアンス/制裁リストチェック **（スタブ: 常に通過）** | エラー |

---

## Agent Design

### FoAgent

**役割:** FoCheck 結果に基づく取引内容の問題調査。BoAgent からの差し戻しへの対応。

**調査観点:**
- 取引内容（日付・金額・通貨・銘柄）の妥当性
- BoAgent 差し戻し理由の評価と説明付与
- 必要に応じて Amend/Cancel イベントを提案（HITL）

**利用可能ツール:**

| ツール | 種別 | 説明 |
|--------|------|------|
| `get_trade_detail` | read | 取引詳細取得 |
| `get_reference_data` | read | 銘柄マスタ参照 |
| `get_counterparty` | read | 取引先情報参照 |
| `get_fo_check_results` | read | FoCheck ルール結果取得 |
| `get_bo_sendback_reason` | read | BoAgent からの差し戻し理由取得 |
| `create_amend_event` | **HITL write** | Amend イベント作成 |
| `create_cancel_event` | **HITL write** | Cancel イベント作成 |
| `provide_explanation` | write | 説明付きで FoValidated に遷移 |
| `escalate_to_fo_user` | write | FoUserToValidate に遷移 |

### BoAgent

**役割:** BoCheck 結果に基づくマスタ・SSI・リスクの問題調査・修正。FO に差し戻すべき問題の特定。

**調査観点:**
- 取引先の有効性（is_active）
- SSI の存在・形式の正確性
- 外部 SSI のルックアップと登録
- FoAgent の説明を考慮した 2 回目以降のトリアージ

**差し戻しルール:**
- BoAgent は 1 回目のトリアージで差し戻しを判断できる（`send_back_to_fo` ツール）
- 同一取引への 2 回目の差し戻しは禁止。代わりに `escalate_to_bo_user` で BoUser に委ねる

**利用可能ツール:**

| ツール | 種別 | 説明 |
|--------|------|------|
| `get_trade_detail` | read | 取引詳細取得 |
| `get_counterparty` | read | 取引先情報参照 |
| `get_settlement_instructions` | read | 登録済み SSI 取得 |
| `lookup_external_ssi` | read | 外部ソース SSI 検索 |
| `get_triage_history` | read | 過去のトリアージ履歴 |
| `get_counterparty_exception_history` | read | CP の過去失敗件数 |
| `get_bo_check_results` | read | BoCheck ルール結果取得 |
| `get_fo_explanation` | read | FoAgent の説明取得（2回目トリアージ時） |
| `register_ssi` | **HITL write** | 新規 SSI 登録 |
| `update_ssi` | **HITL write** | 既存 SSI 修正 |
| `reactivate_counterparty` | **HITL write** | 取引先再有効化 |
| `send_back_to_fo` | **HITL write** | 差し戻し（理由必須、1回目のみ） |
| `escalate_to_bo_user` | write | BoUserToValidate に遷移（2回目以降） |

---

## System Settings

取引チェックのトリガーモードは設定画面から変更可能。

| 設定キー | 値 | 説明 |
|---------|-----|------|
| `fo_check_trigger` | `auto` / `manual` | auto: FoValidated 移行時に自動実行 |
| `bo_check_trigger` | `auto` / `manual` | auto: FoValidated 移行後に自動実行 |

---

## Functional Requirements

### 実装済み（Phase 1〜25）

| ID | 機能 | 状態 |
|----|------|------|
| FR-01 | STP 失敗入力バリデーション（trade_id + error_message） | Done |
| FR-02 | ReAct ループによる動的ツール選択 | Done |
| FR-03 | read-only ツール群（get_trade_detail 等 7 ツール） | Done |
| FR-04 | write ツール群（register_ssi, update_ssi, reactivate_counterparty, escalate） | Done |
| FR-05 | HITL（interrupt_before）による書き込み前承認 | Done |
| FR-06 | 診断レポート生成（root_cause, diagnosis, recommended_action） | Done |
| FR-07 | POST /api/v1/triage エンドポイント | Done |
| FR-08 | POST /api/v1/triage/{run_id}/resume エンドポイント | Done |
| FR-09 | エージェント実行ステップのレスポンス埋め込み | Done |
| FR-10 | DB 永続化（PostgreSQL + Alembic） | Done |
| FR-11 | CRUD API（trades / counterparties / ssis / stp_exceptions / reference_data） | Done |
| FR-12 | 取引・カウンターパーティ・SSI・Ref Data 管理画面 | Done |
| FR-13 | アクセス制御（Nginx Basic Auth + API Key） | Done |
| FR-14 | CI/CD（GitHub Actions → Cloud Run + VM） | Done |

### 新規（Phase 26）

| ID | 機能 | 優先度 |
|----|------|--------|
| FR-15 | 取引 WorkflowStatus 管理（11 ステータス遷移） | Must |
| FR-16 | 取引バージョン管理（Amend/Cancel ごとにインクリメント） | Must |
| FR-17 | FoCheck ルールエンジン（7 ルール） | Must |
| FR-18 | BoCheck ルールエンジン（7 ルール、うち 2 はスタブ） | Must |
| FR-19 | FoAgent 実装（FoCheck 結果トリアージ + 差し戻し対応） | Must |
| FR-20 | BoAgent 実装（BoCheck 結果トリアージ + 差し戻し機能） | Must |
| FR-21 | BoAgent → FoAgent 差し戻し（最大 1 回、2 回目は BoUser にエスカレーション） | Must |
| FR-22 | トレードイベント（Amend / Cancel）の作成・承認 | Must |
| FR-23 | FoAgent による Amend/Cancel イベント作成（HITL） | Must |
| FR-24 | チェックトリガー設定（auto / manual）の管理画面 | Should |
| FR-25 | 取引詳細画面（バージョン履歴・チェック結果・イベント・トリアージボタン） | Must |

---

## Non-Functional Requirements

| Category | Requirement |
|----------|------------|
| **Security** | API keys は `.env` 管理。ハードコード禁止 |
| **Security** | 全外部入力は Pydantic でバリデーション |
| **Security** | write 系ツールは全て HITL 承認後のみ実行 |
| **Security** | エージェントのツール権限は定義された tool list のみ |
| **Auditability** | 全承認・拒否・ツール呼び出しを steps に記録 |
| **Auditability** | 取引バージョン履歴を永続保存（物理削除なし） |
| **Maintainability** | Three-Layer Clean Architecture 遵守 |
| **Maintainability** | 依存ライブラリは pyproject.toml でバージョン固定 |
| **Testability** | Domain 層はフレームワーク依存なしでユニットテスト可能 |
| **Observability** | エージェントの各ステップをログ出力 |

---

## Out of Scope

- 実際の外部システム（Bloomberg, Omgeo, SWIFT）との接続
- リスク枠管理・制裁リストチェックの実装（スタブのみ）
- バッチ処理（複数取引の同時処理）
- メール/Slack 通知
- イベントへのエージェントトリアージ（将来対応、本プロジェクトでは取引のみ）
- 同一取引への複数イベント同時進行（将来対応）

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Agent Framework | LangGraph |
| LLM | Claude claude-sonnet-4-6 (Anthropic) |
| API Framework | FastAPI |
| Database | Neon PostgreSQL + SQLAlchemy 2.0 / Alembic |
| Frontend | React 18 / TypeScript / Vite / React Router v6 |
| Hosting | Cloud Run（バックエンド）+ GCP VM / Nginx（フロントエンド） |
| CI/CD | GitHub Actions |
| Validation | Pydantic v2 |
| Package Manager | uv |
| Testing | pytest |
