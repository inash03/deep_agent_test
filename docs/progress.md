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

## Next Steps

1. **Phase 1: Project Scaffolding** — `pyproject.toml`, `src/` ディレクトリ構成, `.env.example`
2. **Phase 2: Domain Layer** — エンティティ定義（STPFailure, TradeDetail, TriageResult, RootCause enum）
3. **Phase 3: Infrastructure Layer** — LangGraph ReActエージェント + ツール群 + モックデータ + HITL
4. **Phase 4: Presentation Layer** — FastAPI エンドポイント（triage + resume）
