# Architecture

## LangGraph StateGraph — エージェントフロー

```mermaid
flowchart TD
    START([START]) --> agent_node

    agent_node["agent_node\n(LLM: Claude Sonnet)"]

    agent_node -->|"register_ssi tool call"| register_ssi_node
    agent_node -->|"other tool calls\n(get_trade_detail, get_counterparty,\nget_reference_data, get_settlement_instructions,\nlookup_external_ssi)"| read_tools_node
    agent_node -->|"no tool calls\n(final JSON output)"| END_NODE([END])

    read_tools_node["read_tools_node\n(ToolNode — read-only)"]
    read_tools_node --> agent_node

    register_ssi_node["register_ssi_node\n(write — HITL required)"]
    register_ssi_node --> agent_node

    HITL["⏸ interrupt_before\n(operator approval required)"]
    register_ssi_node -.->|"pauses here"| HITL

    classDef hitl fill:#f90,stroke:#c60,color:#000
    class register_ssi_node,HITL hitl
```

### HITL フロー（DB 永続化を含む）

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant LangGraph
    participant PostgreSQL
    participant Operator

    Client->>FastAPI: POST /api/v1/triage
    FastAPI->>LangGraph: graph.invoke(initial_state)
    LangGraph->>LangGraph: ReAct loop (read tools)
    LangGraph->>LangGraph: LLM calls register_ssi
    Note over LangGraph: ⏸ interrupt_before=register_ssi_node
    LangGraph-->>FastAPI: snapshot.next = ("register_ssi_node",)
    FastAPI->>PostgreSQL: INSERT triage_runs (PENDING_APPROVAL)
    FastAPI-->>Client: 200 PENDING_APPROVAL + run_id

    Operator->>Client: Approve or Reject
    Client->>FastAPI: POST /api/v1/triage/{run_id}/resume
    alt approved=true
        FastAPI->>LangGraph: graph.invoke(None, config)
        LangGraph->>LangGraph: register_ssi_node executes
    else approved=false
        FastAPI->>LangGraph: graph.update_state (inject rejection ToolMessage)
        FastAPI->>LangGraph: graph.invoke(None, config)
    end
    LangGraph->>LangGraph: agent_node → final JSON output
    LangGraph-->>FastAPI: COMPLETED
    FastAPI->>PostgreSQL: UPDATE triage_runs (COMPLETED) by run_id
    FastAPI-->>Client: 200 COMPLETED + diagnosis

    Client->>FastAPI: GET /api/v1/triage/history
    FastAPI->>PostgreSQL: SELECT * FROM triage_runs ORDER BY created_at DESC
    FastAPI-->>Client: 200 [{...}, {...}]
```

---

## Clean Architecture — 層構成

```mermaid
graph TB
    subgraph Presentation["Presentation Layer (src/presentation/)"]
        router["router.py\nPOST /api/v1/triage\nPOST /api/v1/triage/{run_id}/resume\nGET /api/v1/triage/history"]
        schemas["schemas.py\nTriageRequest / ResumeRequest\nTriageResponse / TriageHistoryResponse"]
    end

    subgraph Domain["Domain Layer (src/domain/)"]
        entities["entities.py\nSTPFailure, TriageResult, Step\nRootCause enum, TriageStatus enum"]
        interfaces["interfaces.py\nITriageUseCase (abstract)\nstart() / resume()"]
    end

    subgraph Infrastructure["Infrastructure Layer (src/infrastructure/)"]
        usecase["triage_use_case.py\nTriageSTPFailureUseCase\nimplements ITriageUseCase"]
        agent["agent.py\nLangGraph StateGraph\nbuild_graph()"]
        tools["tools.py\n@tool functions × 6\n(5 read-only + 1 write)"]
        mock["mock_store.py\nIn-memory mock data\n5 test scenarios"]
        logging_cfg["logging_config.py\nStructured JSON logging"]

        subgraph DB["db/ (Phase 9)"]
            models["models.py\nTriageRunModel\nTriageStepModel\n(SQLAlchemy ORM)"]
            session["session.py\nget_db() — FastAPI Depends\nMakes Session per request"]
            repository["repository.py\nTriageResultRepository\nsave() / list_recent()"]
        end
    end

    subgraph Storage["Storage"]
        pg[("PostgreSQL\ntriage_runs\ntriage_steps\nalembic_version")]
    end

    router --> schemas
    router --> interfaces
    router --> session
    router --> repository
    usecase --> interfaces
    usecase --> agent
    agent --> tools
    tools --> mock
    repository --> models
    session --> pg
    repository --> pg
```

**層のルール（と今回の実用的な例外）:**
- Infrastructure → Domain のみ参照可
- Domain はフレームワーク依存ゼロ（純粋な Python）
- Presentation は本来 Domain のみ参照すべきだが、DB 永続化（`get_db`, `TriageResultRepository`）を router で直接扱うことで実装を簡潔にしている（学習プロジェクトとしての実用的な選択）

---

## Docker Compose 構成

```mermaid
graph LR
    subgraph docker-compose.yml
        postgres["postgres:16\nport: 5432\nvolume: postgres_data\nhealthcheck: pg_isready"]
        backend["backend\n(python:3.12-slim)\nport: 8000\nalembic upgrade head → uvicorn"]
        frontend["frontend\n(nginx)\nport: 5173"]
        test["test\n(python:3.12-slim)\npytest (unit only)\nprofile: test"]
    end

    postgres -->|"healthcheck 通過後に起動"| backend
    backend -->|"healthcheck 通過後に起動"| frontend
```

**各サービスの起動順序:**
1. `postgres` — healthcheck（`pg_isready`）が通るまで待機
2. `backend` — `alembic upgrade head` で migration 適用 → `uvicorn` 起動
3. `frontend` — backend の healthcheck 通過後に nginx 起動

**テストサービス（`test` profile）:**
```bash
# 通常の up には含まれない。明示的に実行する
docker compose --profile test run test
```

---

## Alembic マイグレーション

### ファイル構成

```
alembic.ini                          ← Alembic 設定（sqlalchemy.url は env.py で上書き）
alembic/
  env.py                             ← DATABASE_URL 環境変数を注入、Base.metadata を登録
  script.py.mako                     ← revision ファイルのテンプレート
  versions/
    0001_initial_schema.py           ← triage_runs + triage_steps 作成
```

### migration ライフサイクル

```
1. models.py を変更（例: カラム追加）
      ↓
2. alembic revision --autogenerate -m "add error_code"
      ↓ ← ここで .py ファイルが生成されるだけ（DB は変わらない）
   alembic/versions/0002_add_error_code.py

3. git add + git commit  ← migration ファイルをコード変更と一緒にコミット

4. alembic upgrade head  ← ここで初めて DB に ALTER TABLE が実行される
   （docker compose up 時に backend が自動実行）
```

### DB 状態追跡

Alembic は `alembic_version` テーブルで適用済み revision を追跡する：

```sql
SELECT * FROM alembic_version;
-- version_num
-- -----------
-- 0001          ← 現在このバージョンまで適用済み
```

### よく使うコマンド

| コマンド | 意味 |
|---------|------|
| `alembic upgrade head` | 未適用の migration を全て適用 |
| `alembic downgrade -1` | 直前の migration を1つ取り消し |
| `alembic revision --autogenerate -m "説明"` | モデルとDB差分から migration ファイル生成 |
| `alembic history` | migration 履歴を一覧表示 |
| `alembic current` | 現在 DB に適用済みの revision を確認 |

---

## DB スキーマ

```mermaid
erDiagram
    triage_runs {
        UUID id PK
        VARCHAR trade_id
        VARCHAR status
        VARCHAR run_id "LangGraph thread_id (INDEX)"
        TEXT pending_action_description
        TEXT diagnosis
        VARCHAR root_cause
        TEXT recommended_action
        BOOLEAN action_taken
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }
    triage_steps {
        INT id PK
        UUID triage_run_id FK
        INT position "ステップ順序"
        VARCHAR step_type "tool_call / hitl_prompt / hitl_response"
        VARCHAR name "ツール名"
        JSONB input
        JSONB output
        BOOLEAN approved
    }
    triage_runs ||--o{ triage_steps : "1対多 (cascade delete)"
```

---

## ツール一覧

| ツール名 | 種別 | 説明 |
|---------|------|------|
| `get_trade_detail` | read | トレード詳細取得 |
| `get_counterparty` | read | カウンターパーティ情報取得 |
| `get_reference_data` | read | 銘柄リファレンスデータ取得 |
| `get_settlement_instructions` | read | 登録済みSSI取得 |
| `lookup_external_ssi` | read | 外部ソースからSSI検索 |
| `register_ssi` | **write** | SSI登録（HITL必須） |

---

## API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| `POST` | `/api/v1/triage` | トリアージ開始。COMPLETED または PENDING_APPROVAL を返す |
| `POST` | `/api/v1/triage/{run_id}/resume` | HITL 承認/拒否後の再開 |
| `GET` | `/api/v1/triage/history` | DB に保存されたトリアージ履歴を返す（新しい順） |

---

## AgentState (LangGraph)

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # メッセージ履歴
    trade_id: str        # 調査対象トレードID
    error_message: str   # STPエラーメッセージ
    action_taken: bool   # SSI登録が実行されたか
```
