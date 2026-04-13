# STP Exception Triage Agent

LangGraphのReActエージェントが証券STP（Straight-Through Processing）失敗の原因を自律的に調査し、必要に応じてオペレーターの承認（HITL）を経てSSIを登録するデモアプリケーション。

---

## アーキテクチャ概要

詳細は [`docs/architecture.md`](docs/architecture.md) を参照。

**技術スタック:**
- Backend: Python 3.12 / FastAPI / LangGraph / LangChain-Anthropic
- Frontend: React / TypeScript / Vite *(Phase 11 — 実装予定)*
- AI: Claude Sonnet (claude-sonnet-4-6)

**設計:**
- **ReActパターン**: LLMが動的にツールを選択し、ループしながら診断を進める
- **HITL (Human-in-the-Loop)**: 書き込み操作（SSI登録）は必ずオペレーター承認を経由
- **Clean Architecture**: Presentation / Domain / Infrastructure の3層分離

---

## 前提条件

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) または pip
- Node.js 20+ *(フロントエンド使用時)*
- Anthropic APIキー

---

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/inash03/deep_agent_test.git
cd deep_agent_test
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定
```

### 3. Python依存関係のインストール

```bash
uv pip install -e ".[dev]"
# または
pip install -e ".[dev]"
```

---

## 起動方法

### バックエンド (FastAPI)

```bash
uvicorn src.main:app --reload
```

APIドキュメント: http://localhost:8000/docs

---

## APIリファレンス

### `POST /api/v1/triage` — トリアージ開始

```bash
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d '{"trade_id": "TRD-001", "error_message": "SETT FAIL - SSI not found for counterparty LEI 213800QILIUD4ROSUO03"}'
```

**レスポンス例（COMPLETED）:**
```json
{
  "trade_id": "TRD-002",
  "status": "COMPLETED",
  "run_id": "...",
  "diagnosis": "The BIC code registered for this counterparty is malformed...",
  "root_cause": "BIC_FORMAT_ERROR",
  "recommended_action": "Update the BIC in the SSI registry to a valid 8 or 11 character code.",
  "action_taken": false,
  "steps": [...]
}
```

**レスポンス例（PENDING_APPROVAL）:**
```json
{
  "trade_id": "TRD-001",
  "status": "PENDING_APPROVAL",
  "run_id": "ad3c3c35-93b0-47ed-9bde-67ea7f6da6f2",
  "pending_action_description": "Register SSI for LEI '213800QILIUD4ROSUO03' / currency 'USD': BIC=ACMEGB2L, account=GB29NWBK60161331926819",
  "steps": [...]
}
```

### `POST /api/v1/triage/{run_id}/resume` — HITL承認/拒否

`PENDING_APPROVAL` を受け取った後に呼び出す。

```bash
# 承認
curl -X POST http://localhost:8000/api/v1/triage/ad3c3c35-93b0-47ed-9bde-67ea7f6da6f2/resume \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'

# 拒否
curl -X POST http://localhost:8000/api/v1/triage/ad3c3c35-93b0-47ed-9bde-67ea7f6da6f2/resume \
  -H "Content-Type: application/json" \
  -d '{"approved": false}'
```

---

## テストシナリオ（モックデータ）

| Trade ID | エラー内容 | 期待される root_cause | HITL |
|----------|-----------|----------------------|------|
| TRD-001 | SSI未登録 | MISSING_SSI | あり（外部SSI登録） |
| TRD-002 | BICフォーマット不正 | BIC_FORMAT_ERROR | なし |
| TRD-003 | カウンターパーティ未登録 | COUNTERPARTY_NOT_FOUND | なし |
| TRD-004 | 決済日が過去日 | INVALID_VALUE_DATE | なし |
| TRD-005 | 銘柄マスタ未登録 | INSTRUMENT_NOT_FOUND | なし |

---

## テスト実行

```bash
# ユニットテストのみ（LLM不要）
pytest

# インテグレーションテスト（ANTHROPIC_API_KEY 必須）
pytest -m integration
```

---

## Dockerでの起動

```bash
# ビルド & 起動
docker-compose up --build

# バックグラウンド起動
docker-compose up -d --build

# 停止
docker-compose down
```

バックエンド: http://localhost:8000/docs

---

## プロジェクト構成

```
deep_agent_test/
  src/
    main.py               # FastAPI エントリーポイント
    domain/
      entities.py         # ドメインエンティティ・enum
      interfaces.py       # ITriageUseCase 抽象インターフェース
    infrastructure/
      agent.py            # LangGraph ReAct エージェント
      tools.py            # LangChain ツール定義
      mock_store.py       # モックデータストア
      triage_use_case.py  # ITriageUseCase 実装
      logging_config.py   # 構造化JSON ロギング
    presentation/
      router.py           # FastAPI ルーター
      schemas.py          # Pydantic リクエスト/レスポンス
  tests/
    unit/                 # ユニットテスト（LLM不要）
    integration/          # インテグレーションテスト（LLM必要）
  docs/
    architecture.md       # アーキテクチャ図（Mermaid）
    requirements.md       # 要件定義
    tasks.md              # タスク管理
  Dockerfile              # バックエンド用
  docker-compose.yml      # バックエンド + フロントエンド
  pyproject.toml
  .env.example
```
