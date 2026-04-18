# Architecture

## LangGraph StateGraph — エージェントフロー

4 種の HITL ノードを汎化アーキテクチャで管理。`_HITL_TOOL_TO_NODE` dict でルーティングを制御する。

```mermaid
flowchart TD
    START([START]) --> agent_node

    agent_node["agent_node\n(LLM: Claude claude-sonnet-4-6)"]

    agent_node -->|"register_ssi"| register_ssi_node
    agent_node -->|"reactivate_counterparty"| reactivate_node
    agent_node -->|"update_ssi"| update_ssi_node
    agent_node -->|"escalate"| escalate_node
    agent_node -->|"read-only tool calls\n(7 tools)"| read_tools_node
    agent_node -->|"no tool calls\n(final JSON output)"| END_NODE([END])

    read_tools_node["read_tools_node\n(ToolNode — read-only)"]
    read_tools_node --> agent_node

    register_ssi_node["register_ssi_node\n(write — SSI登録)"]
    reactivate_node["reactivate_counterparty_node\n(write — CP再有効化)"]
    update_ssi_node["update_ssi_node\n(write — SSI修正)"]
    escalate_node["escalate_node\n(write — エスカレーション)"]

    register_ssi_node --> agent_node
    reactivate_node --> agent_node
    update_ssi_node --> agent_node
    escalate_node --> agent_node

    HITL["⏸ interrupt_before\n(operator approval required)"]
    register_ssi_node -.->|"pauses"| HITL
    reactivate_node -.->|"pauses"| HITL
    update_ssi_node -.->|"pauses"| HITL
    escalate_node -.->|"pauses"| HITL

    classDef hitl fill:#f90,stroke:#c60,color:#000
    class register_ssi_node,reactivate_node,update_ssi_node,escalate_node,HITL hitl
```

### HITL ルーティング実装

```python
# agent.py
_HITL_TOOL_TO_NODE: dict[str, str] = {
    "register_ssi":            "register_ssi_node",
    "reactivate_counterparty": "reactivate_counterparty_node",
    "update_ssi":              "update_ssi_node",
    "escalate":                "escalate_node",
}

def _route_after_agent(state: AgentState) -> str:
    tool_name = last_tool_call(state)
    if tool_name in _HITL_TOOL_TO_NODE:
        return _HITL_TOOL_TO_NODE[tool_name]   # → HITL ノード
    if tool_name:
        return "read_tools_node"
    return END
```

---

## HITL シーケンス（4 アクション共通）

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant LangGraph
    participant PostgreSQL
    participant Operator

    Client->>FastAPI: POST /api/v1/triage {trade_id, error_message}
    FastAPI->>LangGraph: graph.invoke(initial_state)
    LangGraph->>LangGraph: ReAct ループ（read tools × N 回）
    LangGraph->>LangGraph: LLM が HITL ツールを呼び出す
    Note over LangGraph: ⏸ interrupt_before = [4 HITL nodes]
    LangGraph-->>FastAPI: snapshot.next = ("xxx_node",)
    FastAPI->>PostgreSQL: INSERT triage_runs (PENDING_APPROVAL)
    FastAPI-->>Client: 200 PENDING_APPROVAL\n+ pending_action_description\n+ pending_action_type

    Operator->>Client: UI で承認 or 拒否
    Client->>FastAPI: POST /api/v1/triage/{run_id}/resume {approved}
    alt approved=true
        FastAPI->>LangGraph: graph.invoke(None, config, as_node=hitl_node)
        LangGraph->>LangGraph: HITL ノード実行（DB 書き込み）
    else approved=false
        FastAPI->>LangGraph: graph.update_state（拒否 ToolMessage 注入）
        FastAPI->>LangGraph: graph.invoke(None, config, as_node=hitl_node)
    end
    LangGraph->>LangGraph: agent_node → 最終 JSON 出力
    LangGraph-->>FastAPI: COMPLETED
    FastAPI->>PostgreSQL: UPDATE triage_runs (COMPLETED)
    FastAPI-->>Client: 200 COMPLETED + diagnosis + root_cause
```

---

## Clean Architecture — 層構成

```mermaid
graph TB
    subgraph Presentation["Presentation Layer (src/presentation/)"]
        router["router.py\nPOST /triage\nPOST /triage/{id}/resume\nGET /triage/history"]
        routers["routers/\ntrades.py\ncounterparties.py\nssis.py\nstp_exceptions.py\nreference_data.py\nseed.py"]
        schemas["schemas.py\nTriageRequest/Response\nTradeOut / CounterpartyOut\nSsiOut / StpExceptionOut など"]
    end

    subgraph Domain["Domain Layer (src/domain/)"]
        entities["entities.py\nSTPFailure, TriageResult, Step\nRootCause, TriageStatus\nTradeStatus, StpExceptionStatus"]
        interfaces["interfaces.py\nITriageUseCase\nstart() / resume()"]
    end

    subgraph Infrastructure["Infrastructure Layer (src/infrastructure/)"]
        usecase["triage_use_case.py\nTriageSTPFailureUseCase"]
        agent["agent.py\nLangGraph StateGraph\nbuild_graph()\n_HITL_TOOL_TO_NODE"]
        tools["tools.py\n11 @tool 関数\n(7 read-only + 4 HITL-write)"]
        mock["mock_store.py\nユニットテスト用モック"]
        seed["seed.py\nseed_database()\nreset_and_seed()"]
        secrets["secrets.py\nload_secrets()\nenv / gcp 切り替え"]
        logging_cfg["logging_config.py\n構造化 JSON ロギング"]

        subgraph DB["db/"]
            models["models.py\n7 ORM モデル"]
            session["session.py\nget_db()"]
            repos["*_repository.py\n× 6 リポジトリ"]
        end
    end

    subgraph Storage["Storage"]
        neon[("Neon PostgreSQL\n7 tables")]
    end

    router --> interfaces
    routers --> repos
    usecase --> interfaces
    usecase --> agent
    agent --> tools
    tools --> mock
    tools --> repos
    repos --> models
    session --> neon
    repos --> neon
```

**層のルール:**
- Infrastructure → Domain のみ参照可
- Domain はフレームワーク依存ゼロ（純粋な Python）
- Presentation は Domain インターフェース経由でユースケースを呼び出す

---

## インフラ構成（本番環境）

```mermaid
graph LR
    User["ブラウザ"] -->|"HTTPS / Basic Auth"| VM

    subgraph GCP_VM["GCP VM (e2-micro)"]
        nginx["Nginx\nport 5173\nBasic Auth\n静的フロントエンド配信"]
    end

    nginx -->|"API リクエスト\nX-API-Key ヘッダー"| CloudRun

    subgraph CloudRun["Cloud Run (us-central1)"]
        fastapi["FastAPI\n+ LangGraph Agent\nport 8000"]
    end

    fastapi -->|"DATABASE_URL"| Neon
    fastapi -->|"ANTHROPIC_API_KEY"| Anthropic

    subgraph External["外部サービス"]
        Neon[("Neon PostgreSQL")]
        Anthropic["Anthropic API\n(Claude claude-sonnet-4-6)"]
    end

    subgraph CICD["CI/CD (GitHub Actions)"]
        GHA["push to main\n→ Cloud Run デプロイ\n→ VM SSH でフロント更新"]
    end
```

**アクセス制御:**
- フロントエンド: Nginx Basic Auth（`APP_USERNAME` / `APP_PASSWORD`）
- バックエンド LLM エンドポイント: `X-API-Key` ヘッダー必須（`API_KEY` 環境変数）
- `/health`, `/docs` は認証不要

---

## Docker Compose 構成（開発・CI）

バックエンドは Cloud Run で稼働するため、`docker-compose.yml` はフロントエンドとテストのみ管理する。

```mermaid
graph LR
    subgraph docker-compose.yml
        frontend["frontend\n(nginx:alpine)\nport: 5173\nBasic Auth"]
        test["test\n(python:3.12-slim)\npytest (unit only)\nprofile: test"]
    end

    frontend -->|"API リクエスト転送"| CloudRun["Cloud Run\n(バックエンド)"]
```

```bash
# フロントエンドのみ起動
docker compose up --build -d

# ユニットテスト実行
docker compose --profile test run test
```

---

## Alembic マイグレーション

```
alembic/versions/
  0001_initial_schema.py     # triage_runs + triage_steps
  0002_add_domain_tables.py  # trades / counterparties /
                             # settlement_instructions /
                             # reference_data / stp_exceptions
```

```bash
alembic upgrade head       # 未適用 migration を全て適用
alembic downgrade -1       # 直前の migration を 1 つ取り消し
alembic history            # migration 履歴一覧
alembic current            # 現在 DB に適用済みの revision
```

---

## DB スキーマ

```mermaid
erDiagram
    triage_runs {
        UUID id PK
        VARCHAR trade_id
        VARCHAR status
        VARCHAR run_id "LangGraph thread_id"
        TEXT pending_action_description
        VARCHAR pending_action_type
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
        INT position
        VARCHAR step_type
        VARCHAR name
        JSONB input
        JSONB output
        BOOLEAN approved
    }
    trades {
        VARCHAR trade_id PK
        VARCHAR counterparty_lei
        VARCHAR instrument_id
        VARCHAR currency
        NUMERIC amount
        DATE value_date
        DATE trade_date
        VARCHAR settlement_currency
        VARCHAR stp_status
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }
    counterparties {
        VARCHAR lei PK
        VARCHAR name
        VARCHAR bic
        BOOLEAN is_active
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }
    settlement_instructions {
        UUID id PK
        VARCHAR lei
        VARCHAR currency
        VARCHAR bic
        VARCHAR account
        VARCHAR iban
        BOOLEAN is_external
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }
    reference_data {
        VARCHAR instrument_id PK
        VARCHAR description
        VARCHAR asset_class
        BOOLEAN is_active
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }
    stp_exceptions {
        UUID id PK
        VARCHAR trade_id
        TEXT error_message
        VARCHAR status
        UUID triage_run_id
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    triage_runs ||--o{ triage_steps : "cascade delete"
    trades ||--o{ stp_exceptions : "soft ref (no FK)"
    counterparties ||--o{ settlement_instructions : "lei"
```

---

## ツール一覧

| ツール名 | 種別 | 説明 |
|---------|------|------|
| `get_trade_detail` | read | トレード詳細取得（DB / mock fallback） |
| `get_settlement_instructions` | read | 登録済み SSI 取得 |
| `get_reference_data` | read | 銘柄リファレンスデータ取得 |
| `get_counterparty` | read | カウンターパーティ情報取得 |
| `lookup_external_ssi` | read | 外部ソースから SSI 検索 |
| `get_triage_history` | read | 同一取引の過去トリアージ結果 |
| `get_counterparty_exception_history` | read | 直近 30 日の CP 別 STP 失敗件数 |
| `register_ssi` | **HITL write** | 新規 SSI 登録 |
| `update_ssi` | **HITL write** | 既存 SSI の BIC / 口座番号 / IBAN 修正 |
| `reactivate_counterparty` | **HITL write** | 非アクティブ CP を再有効化 |
| `escalate` | **HITL write** | 担当者エスカレーション |

---

## AgentState（LangGraph）

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str        # 調査対象トレード ID
    error_message: str   # STP エラーメッセージ
    action_taken: bool   # HITL アクションが実行されたか
```

---

## フロントエンド画面一覧

| 画面 | パス | 説明 |
|------|------|------|
| TriagePage | `/` | トリアージ実行・HITL 承認 UI |
| TriageHistoryPage | `/history` | トリアージ履歴（展開でフル診断表示） |
| TradeListPage | `/trades` | 取引一覧・フィルタ |
| StpExceptionListPage | `/stp-exceptions` | STP 例外一覧・トリアージ起動 |
| StpExceptionCreatePage | `/stp-exceptions/new` | STP 例外手動登録 |
| CounterpartyListPage | `/counterparties` | CP 一覧・フィルタ |
| CounterpartyEditPage | `/counterparties/:lei` | CP 編集（name/BIC/is_active） |
| SsiListPage | `/ssis` | SSI 一覧（内部/外部フィルタ） |
| SsiEditPage | `/ssis/:id` | 内部 SSI 編集（BIC/account/IBAN） |
| ReferenceDataListPage | `/reference-data` | 銘柄マスタ一覧（参照のみ） |
