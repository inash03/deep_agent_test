# Requirements

---

## Project Overview

**Name:** deep_agent_test
**Purpose:** LangGraphのDeep Agent（StateGraph / multi-step reasoning agent）を学習するためのサンプルプロジェクト。
証券会社のホールセール業務（FX取引照合・SWIFT生成）をユースケースとして、
LangGraphの主要コンセプト（StateGraph, nodes, edges, tools, conditional routing）を手を動かして理解することを目標とする。

---

## Goals

1. LangGraph の `StateGraph` を使ってagentを構築・実行できるようになる
2. Tool使用・Multi-step reasoning の動作を理解する
3. 条件分岐エッジ（`conditional_edges`）によるフロー制御を理解する
4. Clean Architecture に従ったPythonバックエンド構成を実践する
5. FastAPI経由でagentを呼び出すAPIエンドポイントを実装する

---

## Use Case: FX Trade Confirmation Matching Agent

### Overview

FX Spot / Forward取引のコンファメーション照合を行うエージェント。
自社側トレードと相手方（counterparty）側トレードの2つのメッセージを受け取り、
フィールドごとに照合する。不一致がある場合はSWIFT MT300ドラフトを生成して返す。

### Agent Flow

```
[Input]
  our_trade + counterparty_trade
        |
        v
[Node: validate_input]
  Pydanticバリデーション
        |
        v
[Node: compare_fields]
  (Tool) compare_fx_fields
  比較対象フィールド:
    - transaction_type (Spot / Forward)
    - currency_pair (bought/sold currency)
    - notional_amount (bought/sold)
    - exchange_rate
    - value_date
    - trade_date
    - counterparty_bic
    - payment_instructions
        |
        v
  ┌─────────────┐
  │ Matched?    │
  └──────┬──────┘
   YES   │   NO
    v    │    v
[MATCHED]  [Node: generate_swift_draft]
           (Tool) generate_mt300_draft
           MT300フォーマットのドラフトテキスト生成
                |
                v
          [Node: output]
          mismatch fields + MT300 draft

[Output]
  status: MATCHED | MISMATCHED
  mismatches: list of mismatched fields (if any)
  swift_draft: MT300 draft text (if mismatched)
  steps: list of executed steps (for observability)
```

### MT300 Key Fields (Mandatory)

| Tag | Field | Example |
|-----|-------|---------|
| :15A: | General Information | sequence header |
| :20: | Transaction Reference | `TRN20240403001` |
| :21: | Related Reference | counterparty ref |
| :22A: | Type of Operation | `NEWT` |
| :94A: | Scope of Operation | `AGRE` |
| :17T: | Fund/Sell Indicator | `B` / `S` |
| :30T: | Trade Date | `20240403` |
| :30V: | Value Date | `20240405` |
| :36: | Exchange Rate | `151.50` |
| :32B: | Currency/Amount Bought | `USD1000000` |
| :33B: | Currency/Amount Sold | `JPY151500000` |
| :57A: | Account With Institution | BIC of receiving bank |
| :58A: | Beneficiary Institution | final beneficiary BIC |

---

## Functional Requirements

| ID | Feature | Priority | Status |
|----|---------|----------|--------|
| FR-01 | FXトレードの入力バリデーション（Pydantic） | Must | Backlog |
| FR-02 | フィールドごとの照合ロジック（compare_fx_fields tool） | Must | Backlog |
| FR-03 | 照合結果の返却（MATCHED / MISMATCHED + 不一致フィールドリスト） | Must | Backlog |
| FR-04 | 不一致時のSWIFT MT300ドラフト生成（generate_mt300_draft tool） | Must | Backlog |
| FR-05 | LangGraph StateGraph による上記フローの実装 | Must | Backlog |
| FR-06 | FastAPI エンドポイント `POST /api/v1/match` | Must | Backlog |
| FR-07 | エージェント実行ステップのレスポンスへの埋め込み | Should | Backlog |
| FR-08 | FX Forward (非Spot) の追加フィールド対応（forward_points等） | Could | Backlog |

---

## Non-Functional Requirements

| Category | Requirement |
|----------|------------|
| **Security** | API keysは`.env`管理。ハードコード禁止 |
| **Security** | 全外部入力はPydanticでバリデーション |
| **Security** | Agentのtool権限は照合・生成ロジックのみに限定 |
| **Maintainability** | Three-Layer Clean Architecture遵守（cross-layer import禁止） |
| **Maintainability** | 依存ライブラリはpyproject.tomlでバージョン固定 |
| **Testability** | Domain層はフレームワーク依存なしでユニットテスト可能にする |
| **Observability** | エージェントの各ステップ（node名・入出力）をログ出力する |

---

## Out of Scope (今回)

- フロントエンド（React）— 後フェーズで追加予定
- 認証・認可（Auth）
- 本番環境へのデプロイ
- データベース永続化（最初はin-memoryのみ）
- 実際のSWIFTネットワーク接続
- CLS照合との統合
- NettingやSplit settlement

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
