# Requirements

---

## Project Overview

**Name:** deep_agent_test
**Purpose:** LangGraphのDeep Agent（ReAct / multi-step reasoning agent）を学習するためのサンプルプロジェクト。
LangGraphの主要コンセプト（StateGraph, nodes, edges, tools, memory）を手を動かして理解することを目標とする。

---

## Goals

1. LangGraph の `StateGraph` を使ってagentを構築・実行できるようになる
2. Tool使用・Multi-step reasoning の動作を理解する
3. Clean Architecture に従ったPythonバックエンド構成を実践する
4. FastAPI経由でagentを呼び出すAPIエンドポイントを実装する

---

## Functional Requirements

> 具体的な機能要件は実装フェーズ開始前に詳細化する。以下は現時点の方向性。

| ID | Feature | Priority | Status |
|----|---------|----------|--------|
| FR-01 | LangGraph StateGraph を使ったシンプルなReActエージェント | Must | TBD |
| FR-02 | エージェントにツール（Web検索、計算など）を持たせる | Must | TBD |
| FR-03 | FastAPI エンドポイント経由でエージェントを呼び出す | Must | TBD |
| FR-04 | エージェントの実行ログ・中間ステップを確認できる | Should | TBD |
| FR-05 | 会話履歴（memory）のサポート | Could | TBD |

---

## Non-Functional Requirements

| Category | Requirement |
|----------|------------|
| **Security** | API keysは`.env`管理。ハードコード禁止 |
| **Security** | 全外部入力はPydanticでバリデーション |
| **Security** | Agentのtool権限は最小限に制限 |
| **Maintainability** | Three-Layer Clean Architecture遵守（cross-layer import禁止） |
| **Maintainability** | 依存ライブラリはpyproject.tomlでバージョン固定 |
| **Testability** | Domain層はフレームワーク依存なしでユニットテスト可能にする |
| **Observability** | エージェントの各ステップをログ出力する |

---

## Out of Scope (今回)

- フロントエンド（React）— 後フェーズで追加予定
- 認証・認可（Auth）
- 本番環境へのデプロイ
- データベース永続化（最初はin-memoryのみ）

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
