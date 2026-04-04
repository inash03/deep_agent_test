# Progress Log

This file is updated by Claude at the end of every development step.

---

## Current Status

**Phase:** Use Case Definition (完了)
**Branch:** `claude/setup-langgraph-project-oXB7j`
**Last updated:** 2026-04-04

---

## Completed Steps

### Step 0 — Development Rules Setup (2026-04-03)

**What was done:**
- Created `CLAUDE.md` with full development rules:
  - Development process guidelines
  - Git conventions (Conventional Commits + Claude authorship footer)
  - Three-Layer Clean Architecture definition (Presentation / Domain / Infrastructure)
  - Package structure
  - Naming conventions (Python snake_case / PascalCase)
  - Security rules (API key management, Pydantic validation, dependency pinning, LangGraph agent safety)
- Created `docs/progress.md` (this file)
- Created `docs/requirements.md` with project overview and initial requirements
- Created `docs/tasks.md` with initial task backlog

---

### Step 1 — Use Case Definition: STP Exception Triage Agent (2026-04-04)

**What was done:**
- ユースケースを **STP Exception Triage Agent** に確定
- `docs/requirements.md` を全面更新:
  - ユースケース概要: STP失敗トレードの原因診断・修正（HITL付き）
  - なぜLLMが必要かの理由を明示
  - ReActパターンによるAgent Flow（analyze → reason/act loop → HITL → output）
  - `RootCause` enum定義（MISSING_SSI, BIC_FORMAT_ERROR等6種）
  - ツール定義6個（read-only 5個 + write 1個）
  - HITLデザイン（register_ssi前の必須承認、監査証跡）
  - 機能要件 FR-01〜FR-10
  - エンドポイント設計（POST /api/v1/triage + POST /api/v1/triage/{run_id}/resume）
- `docs/tasks.md` を全面更新:
  - Phase 1〜6 の具体的タスクリストを再定義
  - HITLフローに対応したPhase 3/4のタスクを追加

**Key design decisions:**
- エージェントはReActパターン（LLMが動的にtoolを選択し、ループするかも自分で判断）
- `register_ssi` のみ書き込みあり → `interrupt_before` で必ずHITL
- モックデータをin-memoryで実装（Phase 3で定義）
- HITLの承認/拒否用にrun_idベースの再開エンドポイントを設計

---

### Step 2 — Phase 1: Project Scaffolding (2026-04-04)

**What was done:**
- `pyproject.toml` 作成（ピン止めバージョン）:
  - Runtime: langgraph==1.1.6, langchain-anthropic==1.4.0, fastapi==0.135.3, uvicorn==0.43.0, pydantic==2.12.5, python-dotenv==1.2.2
  - Dev: pytest==9.0.2, httpx==0.28.1, ruff==0.15.9, mypy==1.20.0
- `src/` ディレクトリ構成作成:
  - `src/presentation/`, `src/domain/`, `src/infrastructure/` (各`__init__.py`付き)
- `tests/unit/`, `tests/integration/` 作成（各`__init__.py`付き）
- `.env.example` 作成（`ANTHROPIC_API_KEY=`のみ）
- `.gitignore` に `.env` が含まれていることを確認済み

---

### Step 3 — Phase 2: Domain Layer (2026-04-04)

**What was done:**
- `src/domain/entities.py` 作成:
  - `RootCause` enum（MISSING_SSI, BIC_FORMAT_ERROR, INVALID_VALUE_DATE, INSTRUMENT_NOT_FOUND, COUNTERPARTY_NOT_FOUND, UNKNOWN）
  - `TriageStatus` enum（COMPLETED, PENDING_APPROVAL）
  - `STPFailure`（入力エンティティ: trade_id, error_message）
  - `TradeDetail`（トレード詳細: counterparty_lei, instrument_id, currency, amount, value_date, settlement_currency）
  - `SettlementInstruction`（SSI: lei, currency, bic, account, iban）
  - `ReferenceData`（銘柄リファレンス: instrument_id, description, asset_class, is_active）
  - `Counterparty`（カウンターパーティマスタ: lei, name, bic, is_active）
  - `Step`（observability用: step_type, name, input, output, approved）
  - `TriageResult`（出力: trade_id, status, run_id, diagnosis, root_cause, recommended_action, action_taken, steps）
- `src/domain/interfaces.py` 作成:
  - `ITriageUseCase` 抽象クラス（`start(failure)` / `resume(run_id, approved)` の2フェーズ設計）
  - HITLフローの設計方針をdocstringで明文化

---

### Step 4 — Phase 3a: Mock Data Store + Tools (2026-04-04)

**What was done:**
- `src/infrastructure/mock_store.py` 作成:
  - 5つのテストシナリオに対応したin-memoryデータ（TRD-001〜TRD-005）
  - `_TRADES`, `_SSIS`, `_COUNTERPARTIES`, `_REFERENCE_DATA`, `_EXTERNAL_SSIS`
  - 公開クエリ関数: `get_trade`, `get_ssi`, `get_reference`, `get_counterparty`, `get_external_ssi`, `register_ssi`
- `src/infrastructure/tools.py` 作成:
  - read-only tools × 5: `get_trade_detail`, `get_settlement_instructions`, `get_reference_data`, `get_counterparty`, `lookup_external_ssi`
  - write tool × 1: `register_ssi`（HITL承認後のみ呼び出し想定）
  - `ALL_TOOLS`, `READ_ONLY_TOOLS`, `WRITE_TOOLS` エクスポート
  - 各ツールはJSON文字列を返す（LLMが解釈しやすい形式）

---

### Step 5 — Phase 3b: LangGraph Agent (2026-04-04)

**What was done:**
- `src/infrastructure/agent.py` 作成:
  - `AgentState` TypedDict（messages: add_messages reducer, trade_id, error_message, action_taken）
  - `SYSTEM_PROMPT`: 調査手順・最終出力JSONフォーマットをLLMに指示
  - `_route_after_agent`: 条件分岐ルーター（register_ssi呼び出し → HITL / 他ツール → read_tools / ツールなし → END）
  - `agent_node`: システムプロンプトを先頭挿入してLLMを呼び出すノード
  - `read_tools_node`: `ToolNode`（read-onlyツール5個）
  - `register_ssi_node`: register_ssiを実行し `action_taken=True` を設定するカスタムノード
  - `build_graph()`: `MemorySaver` + `interrupt_before=["register_ssi_node"]` でコンパイル
- HITLフロー設計:
  - 承認時: `graph.invoke(None, config)` でそのまま継続
  - 拒否時: `graph.update_state()` でrejection ToolMessageを注入後 `graph.invoke(None, config)` で継続（`TriageSTPFailureUseCase` が担当）

### Step 6 — Phase 3c: TriageSTPFailureUseCase + pyproject.toml fix (2026-04-05)

**What was done:**
- `pyproject.toml` 修正: `hatchling` → `setuptools>=68`（Windows + uv/pip editable install互換性問題を解決）
- `src/infrastructure/triage_use_case.py` 作成:
  - `TriageSTPFailureUseCase(ITriageUseCase)` 実装:
    - `start(failure)`: UUID生成 → graph.invoke → HITL検出 → PENDING_APPROVAL or COMPLETED返却
    - `resume(run_id, approved)`: 拒否時はToolMessage注入 → graph.invoke → COMPLETED返却
    - `_build_result()`: `snapshot.next` で中断状態を判定
    - `_pending_result()`: pending_action_descriptionにSSI登録内容を表示
    - `_completed_result()`: LLM最終メッセージをJSONパース
  - `_parse_llm_output()`: 最後のAIMessage（tool_callなし）からJSON抽出、markdown fenceにも対応
  - `_extract_steps()`: AIMessage tool_calls × ToolMessage resultsをStepリストに変換
  - `_format_ssi_action()`: HITL確認メッセージ生成

## Current Status

**Phase:** Phase 3 完了 → Phase 4 (Presentation Layer) 開始待ち
**Branch:** `claude/setup-langgraph-project-oXB7j`
**Last updated:** 2026-04-05

---

### Step 7 — Phase 4: Presentation Layer (2026-04-05)

**What was done:**
- `src/presentation/schemas.py` 作成:
  - `TriageRequest`（trade_id, error_message）
  - `ResumeRequest`（approved: bool）
  - `StepOut`（steps要素: step_type, name, input, output）
  - `TriageResponse`（全出力フィールド + `from_domain()` でドメインエンティティから変換）
- `src/presentation/router.py` 作成:
  - `POST /api/v1/triage` — triage開始、COMPLETED or PENDING_APPROVAL を返す
  - `POST /api/v1/triage/{run_id}/resume` — HITL承認/拒否、COMPLETED を返す
  - シングルトン `TriageSTPFailureUseCase` を `Depends(get_use_case)` で注入（MemorySaverをリクエスト間で共有するため）
- `src/main.py` 作成:
  - `load_dotenv()` で `.env` を読み込み
  - FastAPI アプリにルーターを登録

## Current Status

**Phase:** Phase 4 完了（コア実装完了）
**Branch:** `claude/setup-langgraph-project-oXB7j`
**Last updated:** 2026-04-05

---

## Next Steps

1. **動作確認**: `uv pip install -e ".[dev]"` 後、`uvicorn src.main:app --reload` で起動、`/docs` からTRD-001を試す
2. **Phase 5: Testing** — Domain層ユニットテスト + `/api/v1/triage` 統合テスト
3. **Phase 6: Observability** — 構造化ログ
