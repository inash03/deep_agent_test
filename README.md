# STP Exception Triage Agent

LangGraph の ReAct エージェントが証券 STP（Straight-Through Processing）失敗を自律的に調査し、必要に応じてオペレーターの承認（HITL）を経て修正アクションを実行するデモアプリケーション。

---

## アーキテクチャ概要

詳細は [`docs/architecture.md`](docs/architecture.md) を参照。

**技術スタック:**

| レイヤー | 技術 |
|---------|------|
| Backend | Python 3.12 / FastAPI / LangGraph / LangChain-Anthropic |
| Frontend | React 18 / TypeScript / Vite / React Router v6 |
| Database | Neon PostgreSQL（外部マネージド） + SQLAlchemy 2.0 / Alembic |
| AI モデル | Claude claude-sonnet-4-6 |
| Hosting | Cloud Run（バックエンド）+ GCP VM / Nginx（フロントエンド） |
| CI/CD | GitHub Actions（Cloud Run デプロイ + VM SSH） |

**設計の特徴:**
- **ReAct パターン**: LLM が 11 個のツールを動的に選択しながら診断ループを実行
- **汎化 HITL**: 書き込み操作（4 種）はすべてオペレーター承認を経由（`_HITL_TOOL_TO_NODE` で管理）
- **Clean Architecture**: Presentation / Domain / Infrastructure の 3 層分離

### コアコンセプト: チェック → 自動トリアージによる人間確認の削減

FoCheck / BoCheck で失敗したルールは、**失敗チェック名 + エラーメッセージをそのまま FoAgent / BoAgent の入力として渡し、必ずエージェントがトリアージする**。エージェントが自動解決できるケースは人間の確認なしに完結し、判断が必要なケースのみ HITL（Human-in-the-Loop）でオペレーター承認を求める。

```
FoCheck
  → 失敗なし       → FoValidated（人間確認ゼロ）
  → 失敗あり       → FoAgent トリアージ（失敗チェックを error_message として渡す）
                        → 自動解決   → FoValidated
                        → HITL 承認  → FoValidated
                        → 判断困難   → FoUserToValidate
```

> **実装ルール**: FoTriage / BoTriage の `error_message` は空文字禁止（バリデーションエラー）。UI では FoCheck/BoCheck に失敗がない状態でトリアージ開始ボタンを非活性にする。

---

## 前提条件

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) または pip
- Node.js 20+ *(フロントエンド開発時)*
- Anthropic API キー
- PostgreSQL 接続 URL（ローカル開発は Neon 無料枠で可）

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
# .env を編集して必要な値を設定
```

主な環境変数:

| 変数名 | 説明 |
|--------|------|
| `ANTHROPIC_API_KEY` | Anthropic API キー（必須） |
| `DATABASE_URL` | PostgreSQL 接続 URL（必須） |
| `SECRET_BACKEND` | `env`（デフォルト）または `gcp` |
| `CORS_ORIGINS` | 許可する CORS オリジン |
| `API_KEY` | バックエンドの LLM エンドポイント保護用キー |

### 3. Python 依存関係のインストール

```bash
uv pip install -e ".[dev]"
# または
pip install -e ".[dev]"
```

### 4. DB マイグレーション

```bash
alembic upgrade head
```

### 5. シードデータの投入

```bash
python -m src.infrastructure.seed
```

---

## 起動方法

### バックエンド（開発）

```bash
uvicorn src.main:app --reload
```

API ドキュメント: http://localhost:8000/docs

### フロントエンド（開発）

```bash
cd frontend
npm install
npm run dev
```

http://localhost:5173

### Docker Compose（フロントエンドのみ）

バックエンドは Cloud Run 上で動作するため、`docker-compose.yml` はフロントエンド（Nginx）のみ管理する。

```bash
# ビルド & 起動
docker compose up --build -d

# 停止
docker compose down
```

フロントエンド: http://localhost:5173

### テストサービス（ユニットテストのみ）

```bash
docker compose --profile test run test
```

---

## テスト実行

```bash
# ユニットテストのみ（LLM 不要）
pytest

# インテグレーションテスト（ANTHROPIC_API_KEY + DATABASE_URL 必須）
pytest -m integration
```

---

## API リファレンス

### トリアージ

| メソッド | パス | 説明 |
|---------|------|------|
| `POST` | `/api/v1/triage` | トリアージ開始 |
| `POST` | `/api/v1/triage/{run_id}/resume` | HITL 承認/拒否 |
| `GET` | `/api/v1/triage/history` | トリアージ履歴一覧 |

### 取引（Trades）

| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/api/v1/trades` | 一覧（trade_id/stp_status/trade_date フィルタ） |
| `GET` | `/api/v1/trades/{trade_id}` | 単件取得 |

### カウンターパーティ

| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/api/v1/counterparties` | 一覧（lei/name フィルタ） |
| `GET` | `/api/v1/counterparties/{lei}` | 単件取得 |
| `PATCH` | `/api/v1/counterparties/{lei}` | 部分更新（name/bic/is_active） |

### STP 例外

| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/api/v1/stp-exceptions` | 一覧（status/trade_id フィルタ） |
| `POST` | `/api/v1/stp-exceptions` | 作成 |
| `PATCH` | `/api/v1/stp-exceptions/{id}` | ステータス更新 |
| `POST` | `/api/v1/stp-exceptions/{id}/start-triage` | トリアージ開始（例外から直接） |

### SSI（決済指図）

| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/api/v1/ssis` | 一覧（lei/is_external フィルタ） |
| `GET` | `/api/v1/ssis/{id}` | 単件取得 |
| `PATCH` | `/api/v1/ssis/{id}` | 更新（bic/account/iban） |

### リファレンスデータ

| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/api/v1/reference-data` | 銘柄マスタ一覧 |

### 管理

| メソッド | パス | 説明 |
|---------|------|------|
| `POST` | `/api/v1/admin/seed` | 冪等シード（空テーブルのみ） |
| `POST` | `/api/v1/admin/refresh` | 全データをシード状態にリセット |

---

## テストシナリオ（シードデータ）

| Trade ID | STP エラー概要 | root_cause | HITL アクション |
|----------|--------------|------------|----------------|
| TRD-001 | SSI 未登録 | MISSING_SSI | register_ssi |
| TRD-002 | BIC フォーマット不正 | BIC_FORMAT_ERROR | なし |
| TRD-003 | カウンターパーティ未登録 | COUNTERPARTY_NOT_FOUND | なし |
| TRD-004 | 決済日が過去日 | INVALID_VALUE_DATE | なし |
| TRD-005 | 銘柄マスタ未登録 | INSTRUMENT_NOT_FOUND | なし |
| TRD-008 | SWIFT AC01（口座番号不正） | SWIFT_AC01 | update_ssi |
| TRD-009 | SWIFT AG01（CP 非アクティブ） | SWIFT_AG01 | reactivate_counterparty |
| TRD-010 | 複合障害（SSI + CP） | COMPOUND_FAILURE | register_ssi / reactivate |
| TRD-011 | IBAN フォーマット不正 | IBAN_FORMAT_ERROR | update_ssi |
| TRD-012 | SLA タイムアウト（BIC 失効） | UNKNOWN | escalate |

---

## HITL（Human-in-the-Loop）フロー

```
POST /api/v1/triage
  → エージェント調査（ReAct ループ）
    → HITL アクション要求
      → 200 PENDING_APPROVAL + pending_action_description
        → オペレーターが UI で承認 or 拒否
POST /api/v1/triage/{run_id}/resume
  → アクション実行 or キャンセル
  → 200 COMPLETED + diagnosis + root_cause
```

4 種の HITL アクション:

| アクション | 説明 |
|-----------|------|
| `register_ssi` | 新規 SSI 登録（外部ソースから取得した情報で） |
| `update_ssi` | 既存 SSI の BIC / 口座番号 / IBAN を修正 |
| `reactivate_counterparty` | 非アクティブ CP を再有効化 |
| `escalate` | 調査困難なケースを担当者にエスカレーション |

---

## プロジェクト構成

```
deep_agent_test/
  src/
    main.py                    # FastAPI エントリーポイント
    domain/
      entities.py              # ドメインエンティティ・enum
      interfaces.py            # ITriageUseCase 抽象インターフェース
    infrastructure/
      agent.py                 # LangGraph ReAct エージェント（HITL ノード × 4）
      tools.py                 # @tool 定義（11 ツール: 7 read + 4 write/HITL）
      mock_store.py            # ユニットテスト用モックストア
      triage_use_case.py       # ITriageUseCase 実装
      logging_config.py        # 構造化 JSON ロギング
      secrets.py               # Secret Manager 抽象化（env / gcp）
      seed.py                  # DB シード / リセット
      db/
        models.py              # SQLAlchemy ORM（7 テーブル）
        session.py             # get_db() FastAPI Depends
        repository.py          # TriageResultRepository
        trade_repository.py
        counterparty_repository.py
        ssi_repository.py
        stp_exception_repository.py
        reference_data_repository.py
    presentation/
      router.py                # トリアージ用ルーター
      schemas.py               # Pydantic スキーマ
      routers/
        trades.py
        counterparties.py
        ssis.py
        stp_exceptions.py
        reference_data.py
        seed.py                # admin/seed + admin/refresh
  frontend/
    src/
      pages/
        TriagePage.tsx          # メインのトリアージ画面（HITL UI 含む）
        TriageHistoryPage.tsx   # トリアージ履歴
        TradeListPage.tsx
        StpExceptionListPage.tsx
        StpExceptionCreatePage.tsx
        CounterpartyListPage.tsx
        CounterpartyEditPage.tsx
        SsiListPage.tsx
        SsiEditPage.tsx
        ReferenceDataListPage.tsx
      components/
        NavBar.tsx             # 固定ナビバー（スクロール対応）
        PageLayout.tsx
        Pagination.tsx
        StatusBadge.tsx
      api/                     # API クライアント（fetch wrapper）
      types/                   # TypeScript 型定義
      styles/theme.ts          # 共通スタイル定数
  tests/
    unit/                      # ユニットテスト（LLM 不要）
    integration/               # インテグレーションテスト
  alembic/
    versions/
      0001_initial_schema.py   # triage_runs + triage_steps
      0002_add_domain_tables.py # trades / counterparties / ssis / ref_data / stp_exceptions
  docs/
    architecture.md
    requirements.md
    tasks.md
    progress.md
  .github/workflows/
    deploy.yml                 # Cloud Run デプロイ + VM SSH フロントデプロイ
  Dockerfile                   # バックエンド用（multi-stage: production / test）
  docker-compose.yml           # フロントエンド（Nginx）+ テスト
  pyproject.toml
  .env.example
  CLAUDE.md
```
