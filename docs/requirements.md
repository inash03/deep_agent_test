# Requirements

---

## Project Overview

**Name:** deep_agent_test
**Purpose:** LangGraphのDeep Agent（ReActパターン / multi-step reasoning agent）を学習するためのサンプルプロジェクト。
証券会社のホールセール業務（STP失敗トレードの原因診断・修正）をユースケースとして、
LangGraphの主要コンセプト（StateGraph, nodes, edges, tools, conditional routing, HITL）を手を動かして理解することを目標とする。

---

## Goals

1. LangGraph の `StateGraph` + ReActパターンを使ってagentを構築・実行できるようになる
2. LLMが動的にtoolを選択するMulti-step reasoningの動作を理解する
3. 条件分岐エッジ（`conditional_edges`）によるフロー制御を理解する
4. `interrupt_before` / `interrupt_after` によるHuman-in-the-Loop（HITL）を実装できるようになる
5. Clean Architecture に従ったPythonバックエンド構成を実践する
6. FastAPI経由でagentを呼び出すAPIエンドポイントを実装する

---

## Use Case: STP Exception Triage Agent

### Overview

STP（Straight-Through Processing）失敗トレードの原因を自律的に診断し、
修正アクション（SSI登録など）をHITL付きで実行するReActエージェント。

オペレーターがエラーメッセージを解釈して複数システムを手で確認していた作業を代替する。

### Why LLM is Essential

- エラーメッセージの**意味解釈**（どのシステムを調べるべきか判断）
- ツール結果を読んで**次のアクションを動的に決定**（ループが必要かどうかも含む）
- 診断結果を**自然言語でレポート生成**（担当者向け説明）
- エッジケースのハンドリングで**人間への確認事項を適切に表現**

### Agent Flow (ReAct Pattern)

```
[Input]
  trade_id + error_message
        |
        v
[LLM: analyze_error]
  エラーメッセージを解釈し、
  調査すべき仮説を立てる
  → 最初に呼ぶtoolを決定
        |
        v
[ReAct Loop]
  ┌─────────────────────────────────┐
  │                                 │
  │  [LLM: reason]                  │
  │  - 現在の情報を整理             │
  │  - 次に呼ぶtoolを決定           │
  │    (または診断完了と判断)       │
  │          |                      │
  │          v                      │
  │  [Tool Execution]               │
  │  - get_trade_detail             │
  │  - get_settlement_instructions  │
  │  - get_reference_data           │
  │  - get_counterparty             │
  │  - lookup_external_ssi          │
  │          |                      │
  │          v                      │
  │  [LLM: observe]                 │
  │  - ツール結果を解釈             │
  │  - 仮説を更新                   │
  │  - ループ継続 or 終了?          │
  │                                 │
  └──── ループ継続 ────────────────┘
        |
        | 診断完了
        v
[LLM: generate_diagnosis]
  - root_cause を特定
  - recommended_action を生成
        |
        v
  ┌─────────────────────┐
  │ アクション必要?     │
  └──────┬──────────────┘
    NO   │   YES
    v    │    v
[Output] [HITL: interrupt]
         "SSI未登録。外部ソースに
          登録データあり。登録しますか？"
               |
         承認  │  拒否
          v    │    v
  [Tool: register_ssi]  [Output (action skipped)]
          |
          v
       [Output]

[Output]
  trade_id: str
  diagnosis: str          # 自然言語による診断説明
  root_cause: RootCause   # enum (下記参照)
  recommended_action: str # 推奨アクション説明
  action_taken: bool      # HITLで承認されアクション実行したか
  steps: list[Step]       # 実行したtool呼び出しのログ（observability）
```

### Root Cause Types

| Code | 説明 |
|------|------|
| `MISSING_SSI` | カウンターパーティのSSI（Settlement Standing Instructions）が未登録 |
| `BIC_FORMAT_ERROR` | BICコードのフォーマット誤り（例: 8桁vs11桁） |
| `INVALID_VALUE_DATE` | バリューデートが無効（休日、過去日付など） |
| `INSTRUMENT_NOT_FOUND` | リファレンスデータに銘柄が存在しない |
| `COUNTERPARTY_NOT_FOUND` | マスタデータにカウンターパーティが存在しない |
| `UNKNOWN` | 調査したが原因を特定できない |

### Tools (LangGraph Tools)

| Tool | 入力 | 出力 | 副作用 |
|------|------|------|--------|
| `get_trade_detail` | `trade_id: str` | トレード詳細（通貨ペア、金額、バリューデート、counterparty LEI等） | なし（read-only） |
| `get_settlement_instructions` | `lei: str, currency: str` | SSI情報（BIC, account, iban等）またはNot Found | なし（read-only） |
| `get_reference_data` | `instrument_id: str` | 銘柄リファレンス情報 | なし（read-only） |
| `get_counterparty` | `lei: str` | カウンターパーティマスタ情報 | なし（read-only） |
| `lookup_external_ssi` | `lei: str, currency: str` | 外部ソース（Bloomberg/Omgeo相当）からSSI情報を取得 | なし（read-only） |
| `register_ssi` | `lei: str, currency: str, ssi_data: dict` | 登録結果 | **書き込みあり → HITL必須** |

### HITL Design

- `register_ssi` を呼ぶ前に必ず `interrupt_before` でオペレーターに確認
- 確認メッセージには「何を登録しようとしているか」「ソースはどこか」を明示
- 拒否された場合はアクションなしで診断レポートのみ返す
- 全ての承認/拒否は `steps` に記録する（監査証跡）

---

## Functional Requirements

| ID | Feature | Priority | Status |
|----|---------|----------|--------|
| FR-01 | STP失敗通知の入力バリデーション（trade_id + error_message） | Must | Backlog |
| FR-02 | ReActループによる動的ツール選択（LangGraph StateGraph） | Must | Backlog |
| FR-03 | read-onlyツール群の実装（get_trade_detail, get_settlement_instructions, get_reference_data, get_counterparty, lookup_external_ssi） | Must | Backlog |
| FR-04 | write系ツールの実装（register_ssi） | Must | Backlog |
| FR-05 | HITL：register_ssi実行前のオペレーター確認（interrupt_before） | Must | Backlog |
| FR-06 | 診断レポート生成（root_cause, diagnosis, recommended_action） | Must | Backlog |
| FR-07 | FastAPI エンドポイント `POST /api/v1/triage` | Must | Backlog |
| FR-08 | FastAPI エンドポイント `POST /api/v1/triage/{run_id}/resume` （HITL承認/拒否） | Must | Backlog |
| FR-09 | エージェント実行ステップのレスポンスへの埋め込み（observability） | Should | Backlog |
| FR-10 | In-memoryのモックデータストア（実DBなし） | Should | Backlog |

---

## Non-Functional Requirements

| Category | Requirement |
|----------|------------|
| **Security** | API keysは`.env`管理。ハードコード禁止 |
| **Security** | 全外部入力はPydanticでバリデーション |
| **Security** | register_ssiは必ずHITL承認後のみ実行（エージェントが自律実行不可） |
| **Security** | Agentのtool権限は定義されたtool listのみに限定 |
| **Auditability** | 全ての承認・拒否・tool呼び出しをstepsに記録 |
| **Maintainability** | Three-Layer Clean Architecture遵守（cross-layer import禁止） |
| **Maintainability** | 依存ライブラリはpyproject.tomlでバージョン固定 |
| **Testability** | Domain層はフレームワーク依存なしでユニットテスト可能にする |
| **Observability** | エージェントの各ステップ（node名・tool名・入出力）をログ出力する |

---

## Out of Scope (今回)

- フロントエンド（React）— 後フェーズで追加予定
- 認証・認可（Auth）
- 本番環境へのデプロイ
- 実際のデータベース永続化（モックデータのみ）
- 実際の外部システム（Bloomberg, Omgeo, SWIFT）との接続
- 複数エラーの同時処理（バッチ処理）
- メール通知

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Agent Framework | LangGraph (latest stable) |
| LLM | Claude (Anthropic API) |
| API Framework | FastAPI |
| Validation | Pydantic v2 |
| Package Manager | uv |
| Testing | pytest |
| Linting | ruff |
| Type Checking | mypy |
