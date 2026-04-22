# Architecture

## LangGraph エージェント構成

| エージェント | ファイル | 役割 | HITL ノード数 |
|---|---|---|---|
| Legacy Agent | agent.py | STP 例外トリアージ（旧） | 4 |
| FoAgent | fo_agent.py | FoCheck 結果調査 / Amend・Cancel 提案 | 2 |
| BoAgent | bo_agent.py | BoCheck 結果調査 / SSI・CP 修正 / FO 差し戻し | 4 |

## LangGraph StateGraph — エージェントフロー

### Legacy Agent フロー（agent.py）

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

### FoAgent フロー（fo_agent.py）

```mermaid
flowchart TD
    START([START]) --> agent_node

    agent_node["agent_node\n(Claude claude-sonnet-4-6)"]

    agent_node -->|"create_amend_event"| amend_node
    agent_node -->|"create_cancel_event"| cancel_node
    agent_node -->|"read-only tool calls\n(7 tools)"| read_tools_node
    agent_node -->|"no tool calls\n(final output)"| END_NODE([END])

    read_tools_node["read_tools_node\n(ToolNode — read-only)"]
    read_tools_node --> agent_node

    amend_node["create_amend_event_node\n(HITL — Amend イベント作成)"]
    cancel_node["create_cancel_event_node\n(HITL — Cancel イベント作成)"]

    amend_node --> agent_node
    cancel_node --> agent_node

    HITL["⏸ interrupt_before\n(operator approval required)"]
    amend_node -.->|"pauses"| HITL
    cancel_node -.->|"pauses"| HITL

    classDef hitl fill:#f90,stroke:#c60,color:#000
    class amend_node,cancel_node,HITL hitl
```

### BoAgent フロー（bo_agent.py）

```mermaid
flowchart TD
    START([START]) --> agent_node

    agent_node["agent_node\n(Claude claude-sonnet-4-6)"]

    agent_node -->|"register_ssi"| register_node
    agent_node -->|"reactivate_counterparty"| reactivate_node
    agent_node -->|"update_ssi"| update_node
    agent_node -->|"send_back_to_fo"| sendback_node
    agent_node -->|"read-only tool calls\n(8 tools)"| read_tools_node
    agent_node -->|"no tool calls\n(final output)"| END_NODE([END])

    read_tools_node["read_tools_node\n(ToolNode — read-only)"]
    read_tools_node --> agent_node

    register_node["register_ssi_node\n(HITL — SSI 登録)"]
    reactivate_node["reactivate_counterparty_node\n(HITL — CP 再有効化)"]
    update_node["update_ssi_node\n(HITL — SSI 修正)"]
    sendback_node["send_back_to_fo_node\n(HITL — FO 差し戻し)"]

    register_node --> agent_node
    reactivate_node --> agent_node
    update_node --> agent_node
    sendback_node --> agent_node

    HITL["⏸ interrupt_before\n(operator approval required)"]
    register_node -.->|"pauses"| HITL
    reactivate_node -.->|"pauses"| HITL
    update_node -.->|"pauses"| HITL
    sendback_node -.->|"pauses"| HITL

    classDef hitl fill:#f90,stroke:#c60,color:#000
    class register_node,reactivate_node,update_node,sendback_node,HITL hitl
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
        routers["routers/\ntrades.py\ncounterparties.py\nssis.py\nstp_exceptions.py\nreference_data.py\nfo_triage.py\nbo_triage.py\ntrade_events.py\nsettings.py\nseed.py"]
        schemas["schemas.py\nTriageRequest/Response\nTradeOut / CounterpartyOut\nSsiOut / StpExceptionOut\nTradeWorkflowStatus / EventType / CheckResult\nTradeEventOut / TradeVersionOut など"]
    end

    subgraph Domain["Domain Layer (src/domain/)"]
        entities["entities.py\nSTPFailure, TriageResult, Step\nRootCause, TriageStatus\nTradeStatus, StpExceptionStatus\nTradeWorkflowStatus, EventType\nCheckResult, TradeEvent"]
        interfaces["interfaces.py\nITriageUseCase\nstart() / resume()"]
        check_rules["check_rules.py\nFoRule / BoRule × 各 7 ルール"]
    end

    subgraph Infrastructure["Infrastructure Layer (src/infrastructure/)"]
        usecase["triage_use_case.py\nTriageSTPFailureUseCase"]
        fo_usecase["fo_triage_use_case.py\nFoTriageUseCase"]
        bo_usecase["bo_triage_use_case.py\nBoTriageUseCase"]
        agent["agent.py\nLangGraph StateGraph\nbuild_graph()\n_HITL_TOOL_TO_NODE"]
        fo_agent["fo_agent.py\nFoAgent\nbuild_fo_graph()"]
        bo_agent["bo_agent.py\nBoAgent\nbuild_bo_graph()"]
        tools["tools.py\n11 @tool 関数\n(7 read-only + 4 HITL-write)"]
        rule_engine["rule_engine.py\nFoCheck / BoCheck 実行エンジン"]
        mock["mock_store.py\nユニットテスト用モック"]
        seed["seed.py\nseed_database()\nreset_and_seed()"]
        secrets["secrets.py\nload_secrets()\nenv / gcp 切り替え"]
        logging_cfg["logging_config.py\n構造化 JSON ロギング"]

        subgraph DB["db/"]
            models["models.py\n9 テーブル（trades 拡張 + trade_events + app_settings）"]
            session["session.py\nget_db()"]
            repos["*_repository.py\n× 6 リポジトリ"]
            trade_event_repo["trade_event_repository.py"]
            app_setting_repo["app_setting_repository.py"]
            checkpointer["checkpointer.py"]
        end
    end

    subgraph Storage["Storage"]
        neon[("Neon PostgreSQL\n9 tables")]
    end

    router --> interfaces
    routers --> repos
    usecase --> interfaces
    usecase --> agent
    fo_usecase --> fo_agent
    bo_usecase --> bo_agent
    agent --> tools
    fo_agent --> tools
    bo_agent --> tools
    tools --> mock
    tools --> repos
    repos --> models
    trade_event_repo --> models
    app_setting_repo --> models
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
  0001_initial_schema.py         # triage_runs + triage_steps
  0002_add_domain_tables.py      # trades / counterparties /
                                 # settlement_instructions /
                                 # reference_data / stp_exceptions
  0003_add_workflow_schema.py    # trades 拡張（UUID PK・version・workflow_status 等）
                                 # trade_events・app_settings テーブル追加
  0004_fix_focheck_initial_status.py  # FoCheck 初期ステータス修正
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
        UUID id PK
        VARCHAR trade_id
        INT version
        BOOLEAN is_current
        VARCHAR workflow_status
        VARCHAR counterparty_lei
        VARCHAR instrument_id
        VARCHAR currency
        NUMERIC amount
        DATE value_date
        DATE trade_date
        VARCHAR settlement_currency
        VARCHAR stp_status
        INT sendback_count
        JSONB fo_check_results
        JSONB bo_check_results
        TEXT bo_sendback_reason
        TEXT fo_explanation
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
    trade_events {
        UUID id PK
        VARCHAR trade_id
        INT from_version
        INT to_version
        VARCHAR event_type
        VARCHAR workflow_status
        VARCHAR requested_by
        TEXT reason
        JSONB amended_fields
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }
    app_settings {
        VARCHAR key PK
        VARCHAR value
        TEXT description
        TIMESTAMPTZ updated_at
    }

    triage_runs ||--o{ triage_steps : "cascade delete"
    trades ||--o{ stp_exceptions : "soft ref (no FK)"
    counterparties ||--o{ settlement_instructions : "lei"
    trades ||--o{ trade_events : "trade_id"
```

---

## ツール一覧

### Legacy Agent ツール（agent.py）

| ツール名 | 種別 | 説明 |
|---------|------|------|
| `get_trade_detail` | read | トレード詳細取得 |
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

### FoAgent ツール（fo_agent.py）

| ツール名 | 種別 | 説明 |
|---------|------|------|
| `get_trade_detail` | read | トレード詳細取得 |
| `get_reference_data` | read | 銘柄リファレンスデータ取得 |
| `get_counterparty` | read | カウンターパーティ情報取得 |
| `get_fo_check_results` | read | FoCheck ルール結果取得 |
| `get_bo_sendback_reason` | read | BoAgent からの差し戻し理由取得 |
| `get_triage_history` | read | 同一取引の過去トリアージ結果 |
| `get_counterparty_exception_history` | read | 直近 30 日の CP 別 STP 失敗件数 |
| `create_amend_event` | **HITL write** | Amend イベント作成 |
| `create_cancel_event` | **HITL write** | Cancel イベント作成 |
| `provide_explanation` | write | 説明付きで FoValidated に遷移 |
| `escalate_to_fo_user` | write | FoUserToValidate に遷移 |

### BoAgent ツール（bo_agent.py）

| ツール名 | 種別 | 説明 |
|---------|------|------|
| `get_trade_detail` | read | トレード詳細取得 |
| `get_counterparty` | read | カウンターパーティ情報取得 |
| `get_settlement_instructions` | read | 登録済み SSI 取得 |
| `lookup_external_ssi` | read | 外部ソースから SSI 検索 |
| `get_triage_history` | read | 同一取引の過去トリアージ結果 |
| `get_counterparty_exception_history` | read | 直近 30 日の CP 別 STP 失敗件数 |
| `get_bo_check_results` | read | BoCheck ルール結果取得 |
| `get_fo_explanation` | read | FoAgent の説明取得（2 回目トリアージ時） |
| `register_ssi` | **HITL write** | 新規 SSI 登録 |
| `update_ssi` | **HITL write** | 既存 SSI の BIC / 口座番号 / IBAN 修正 |
| `reactivate_counterparty` | **HITL write** | 非アクティブ CP を再有効化 |
| `send_back_to_fo` | **HITL write** | FoAgent に差し戻し（1 回目のみ） |
| `escalate_to_bo_user` | write | BoUserToValidate に遷移 |

---

## AgentState（LangGraph）

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str        # 調査対象トレード ID
    error_message: str   # STP エラーメッセージ
    action_taken: bool   # HITL アクションが実行されたか
```

```python
class FoAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str        # 調査対象トレード ID
    error_message: str   # FoCheck 失敗メッセージ
    action_taken: bool   # HITL アクションが実行されたか

class BoAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str        # 調査対象トレード ID
    error_message: str   # BoCheck 失敗メッセージ
    action_taken: bool   # HITL アクションが実行されたか
```

---

## フロントエンド画面一覧

| 画面 | パス | 説明 |
|------|------|------|
| TriagePage | `/` | トリアージ実行・HITL 承認 UI |
| TriageHistoryPage | `/history` | トリアージ履歴（展開でフル診断表示） |
| TradeListPage | `/trades` | 取引一覧・フィルタ |
| TradeInputPage | `/trades/new` | 取引入力フォーム（新規作成） |
| TradeDetailPage | `/trades/:trade_id` | 取引詳細（4 タブ: FoCheck / BoCheck / Events / Triage） |
| StpExceptionListPage | `/stp-exceptions` | STP 例外一覧・トリアージ起動 |
| StpExceptionCreatePage | `/stp-exceptions/new` | STP 例外手動登録 |
| CounterpartyListPage | `/counterparties` | CP 一覧・フィルタ |
| CounterpartyEditPage | `/counterparties/:lei` | CP 編集（name/BIC/is_active） |
| SsiListPage | `/ssis` | SSI 一覧（内部/外部フィルタ） |
| SsiEditPage | `/ssis/:id` | 内部 SSI 編集（BIC/account/IBAN） |
| ReferenceDataListPage | `/reference-data` | 銘柄マスタ一覧（参照のみ） |
| SettingsPage | `/settings` | FoCheck / BoCheck トリガー設定（auto / manual） |
