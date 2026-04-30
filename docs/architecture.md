# Architecture

## LangGraph StateGraph — エージェントフロー

FoAgent と BoAgent はそれぞれ独立した LangGraph StateGraph を持つ。
BoAgent はハイブリッド構造（決定論的パス + 自律 ReAct パス）を採用している。

### BoAgent フロー（`src/infrastructure/bo_agent.py`）

```mermaid
flowchart TD
    START([START]) --> model_router

    model_router["model_router_node\n(Haiku/Sonnet 自動選択)"]
    model_router --> gather_context

    gather_context["gather_context_node\n(get_bo_check_results + get_trade_detail)\n決定論的データ収集 — LLM 不使用"]
    gather_context -->|"triage_path=AG01"| ag01_handler
    gather_context -->|"triage_path=MISSING_SSI"| lookup_ssi
    gather_context -->|"triage_path=BE01"| be01_handler
    gather_context -->|"triage_path=AM04"| fo_side_handler
    gather_context -->|"triage_path=COMPOUND\nor UNKNOWN"| deep_investigation

    ag01_handler["ag01_handler\n(reactivate_counterparty HITL 準備)"]
    lookup_ssi["lookup_ssi\n(lookup_external_ssi 直呼び)"]
    be01_handler["be01_handler\n(直接 escalate_to_bo_user)"]
    fo_side_handler["fo_side_handler\n(sendback_count で分岐)"]

    lookup_ssi -->|"SSI あり"| prepare_register_ssi
    lookup_ssi -->|"SSI なし"| ssi_not_found_escalate

    prepare_register_ssi["prepare_register_ssi\n(register_ssi HITL 準備)"]
    ssi_not_found_escalate["ssi_not_found_escalate\n(直接 escalate)"]

    ag01_handler --> reactivate_node
    prepare_register_ssi --> register_ssi_node
    fo_side_handler -->|"sendback_count=0"| send_back_node
    fo_side_handler -->|"sendback_count>=1"| agent_node

    deep_investigation["deep_investigation_node\n(自律 ReAct — LLM × N 回)"]
    deep_investigation --> di_register_ssi_node
    deep_investigation --> di_reactivate_node
    deep_investigation --> di_send_back_node
    deep_investigation --> di_update_ssi_node
    deep_investigation -->|"read tools"| deep_investigation
    deep_investigation -->|"完了"| END_NODE([END])

    agent_node["agent_node\n(サマリー生成 — LLM 1回)"]
    agent_node --> END_NODE

    reactivate_node["reactivate_counterparty_node ⏸"]
    register_ssi_node["register_ssi_node ⏸"]
    send_back_node["send_back_to_fo_node ⏸"]
    di_register_ssi_node["di_register_ssi_node ⏸"]
    di_reactivate_node["di_reactivate_counterparty_node ⏸"]
    di_send_back_node["di_send_back_to_fo_node ⏸"]
    di_update_ssi_node["di_update_ssi_node ⏸"]

    reactivate_node --> agent_node
    register_ssi_node --> agent_node
    send_back_node --> agent_node

    classDef hitl fill:#f90,stroke:#c60,color:#000
    classDef det fill:#4af,stroke:#08f,color:#000
    class reactivate_node,register_ssi_node,send_back_node,di_register_ssi_node,di_reactivate_node,di_send_back_node,di_update_ssi_node hitl
    class gather_context,ag01_handler,lookup_ssi,be01_handler,fo_side_handler,prepare_register_ssi,ssi_not_found_escalate det
```

### FoAgent フロー（`src/infrastructure/fo_agent.py`）

```mermaid
flowchart TD
    START([START]) --> model_router
    model_router["model_router_node\n(Haiku/Sonnet 自動選択)"]
    model_router --> gather_context
    gather_context["gather_context_node\n(get_fo_check_results + get_trade_detail)\nLLM 不使用"]
    gather_context --> agent_node
    agent_node["agent_node\n(LLM: ReAct ループ)"]
    agent_node -->|"create_amend_event"| amend_node
    agent_node -->|"create_cancel_event"| cancel_node
    agent_node -->|"read tools"| agent_node
    agent_node -->|"完了"| END_NODE([END])
    amend_node["create_amend_event_node ⏸"]
    cancel_node["create_cancel_event_node ⏸"]
    amend_node --> agent_node
    cancel_node --> agent_node

    classDef hitl fill:#f90,stroke:#c60,color:#000
    class amend_node,cancel_node hitl
```

### 決定論的パス vs 自律パスのコスト比較

| エラー種別 | パス | LLM 呼び出し | コスト目安 |
|-----------|------|-------------|---------|
| AG01 / counterparty_inactive | 決定論的 | summary 1 回 | ~$0.002 |
| MISSING_SSI (外部 SSI あり) | 決定論的 | summary 1 回 | ~$0.002 |
| MISSING_SSI (外部 SSI なし) | 決定論的 | summary 1 回 | ~$0.002 |
| BE01 / format error | 決定論的 | summary 1 回 | ~$0.002 |
| AM04 (sendback=0) | 決定論的 | summary 1 回 | ~$0.002 |
| AM04 (sendback≥1) | 決定論的 | summary 1 回 | ~$0.002 |
| UNKNOWN / COMPOUND | 自律（ReAct） | 2 回以上 | ~$0.01〜0.05 |

---

## HITL シーケンス（FO/BO トリアージ共通）

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant LangGraph
    participant PostgreSQL
    participant Operator

    Client->>FastAPI: POST /api/v1/trades/{id}/bo-triage {error_message}
    FastAPI->>LangGraph: graph.invoke(initial_state)
    LangGraph->>LangGraph: model_router → gather_context（LLM なし）
    LangGraph->>LangGraph: 決定論的ハンドラ or deep_investigation
    Note over LangGraph: ⏸ interrupt_before = [HITL nodes]
    LangGraph-->>FastAPI: snapshot.next = ("xxx_node",)
    FastAPI->>PostgreSQL: INSERT triage_runs (PENDING_APPROVAL)
    FastAPI-->>Client: 200 PENDING_APPROVAL + pending_action_type + cost_log

    Operator->>Client: UI で承認 or 拒否
    Client->>FastAPI: POST /api/v1/trades/{id}/bo-triage/{run_id}/resume {approved}
    alt approved=true
        FastAPI->>LangGraph: graph.invoke(None, config, as_node=snapshot.next[0])
        LangGraph->>LangGraph: HITL ノード実行（DB 書き込み）
    else approved=false
        FastAPI->>LangGraph: graph.update_state（拒否 ToolMessage 注入）
        FastAPI->>LangGraph: graph.invoke(None, config, as_node=snapshot.next[0])
    end
    LangGraph->>LangGraph: agent_node → サマリー生成
    LangGraph-->>FastAPI: COMPLETED
    FastAPI->>PostgreSQL: INSERT llm_cost_logs（コスト保存）
    FastAPI->>PostgreSQL: UPDATE triage_runs (COMPLETED)
    FastAPI-->>Client: 200 COMPLETED + diagnosis + triage_path + total_cost_usd
```

---

## Clean Architecture — 層構成

```mermaid
graph TB
    subgraph Presentation["Presentation Layer (src/presentation/)"]
        router["router.py (レガシー)\nPOST /triage + resume"]
        routers["routers/\ntrades.py / trade_events.py\nfo_triage.py / bo_triage.py\ncounterparties.py / ssis.py\nstp_exceptions.py / settings.py\nrules.py / cost.py / seed.py"]
        schemas["schemas.py\nTradeOut / TradeEventOut\nCheckResultsResponse\nCostSummaryResponse など"]
    end

    subgraph Domain["Domain Layer (src/domain/)"]
        entities["entities.py\nTradeWorkflowStatus / EventType\nCheckResult / TradeEvent\nSTPFailure / TriageResult / Step\nRootCause / TriageStatus"]
        check_rules["check_rules.py\nFoRule × 9 / BoRule × 8"]
        interfaces["interfaces.py\nITriageUseCase"]
    end

    subgraph Infrastructure["Infrastructure Layer (src/infrastructure/)"]
        fo_uc["fo_triage_use_case.py\nFoTriageUseCase"]
        bo_uc["bo_triage_use_case.py\nBoTriageUseCase"]
        fo_agent["fo_agent.py\nbuild_fo_graph()\nFoAgentState"]
        bo_agent["bo_agent.py\nbuild_bo_graph()\nBoAgentState\n_determine_triage_path()"]
        rule_engine["rule_engine.py\nrun_fo_check()\nrun_bo_check()\nmaybe_run_*()"]
        tools["tools.py\nFO_ALL_TOOLS / BO_ALL_TOOLS\n@tool 関数群"]
        cost_tracker["utils/cost_tracker.py\ncalc_cost()\nselect_model()\ncall_with_cost_tracking()"]
        mock["mock_store.py\nユニットテスト用モック\nTRD-001〜013"]
        seed["seed.py\nseed_database()\nreset_and_seed()"]
        secrets["secrets.py\nload_secrets()"]
        logging_cfg["logging_config.py\n構造化 JSON ロギング"]

        subgraph DB["db/"]
            models["models.py\n11 ORM モデル"]
            session["session.py\nget_db()"]
            repos["*_repository.py × 9\ntrade / counterparty / ssi\nstp_exception / reference_data\ntrade_event / app_setting\nllm_cost_log / triage_run"]
        end
    end

    subgraph Storage["Storage"]
        neon[("Neon PostgreSQL\n11 tables")]
    end

    routers --> fo_uc
    routers --> bo_uc
    routers --> rule_engine
    routers --> repos
    fo_uc --> fo_agent
    bo_uc --> bo_agent
    fo_agent --> tools
    bo_agent --> tools
    fo_agent --> cost_tracker
    bo_agent --> cost_tracker
    rule_engine --> check_rules
    rule_engine --> repos
    tools --> mock
    tools --> repos
    repos --> models
    session --> neon
    repos --> neon
```

**層のルール:**
- Infrastructure → Domain のみ参照可
- Domain はフレームワーク依存ゼロ（純粋な Python）
- Presentation → Infrastructure はユースケース経由のみ

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
  0001_initial_schema.py          # triage_runs + triage_steps
  0002_add_domain_tables.py       # trades / counterparties / settlement_instructions
                                  # reference_data / stp_exceptions
  0003_add_workflow_schema.py     # trades に uuid id / version / workflow_status /
                                  # is_current / fo_check_results / bo_check_results 等追加
                                  # trade_events / app_settings テーブル追加
  0004_fix_focheck_initial_status.py  # データ修正 migration（FoAgentToCheck→FoCheck）
  0005_drop_stp_status.py         # trades.stp_status カラム削除
  0006_add_llm_cost_log.py        # llm_cost_logs テーブル追加
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
        VARCHAR run_id
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
        INT sendback_count
        VARCHAR counterparty_lei
        VARCHAR instrument_id
        VARCHAR currency
        NUMERIC amount
        DATE value_date
        DATE trade_date
        VARCHAR settlement_currency
        JSONB fo_check_results
        JSONB bo_check_results
        TEXT bo_sendback_reason
        TEXT fo_explanation
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
    llm_cost_logs {
        UUID id PK
        VARCHAR run_id
        VARCHAR trade_id
        VARCHAR agent_type
        VARCHAR node
        VARCHAR model
        INT input_tokens
        INT output_tokens
        FLOAT cost_usd
        TEXT reason
        TIMESTAMPTZ created_at
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
    trades ||--o{ trade_events : "trade_id (soft ref)"
    counterparties ||--o{ settlement_instructions : "lei"
```

---

## ツール一覧

### FO エージェント用ツール（`FO_ALL_TOOLS`）

| ツール名 | 種別 | 説明 |
|---------|------|------|
| `get_trade_detail` | read | 取引詳細取得 |
| `get_reference_data` | read | 銘柄マスタ参照 |
| `get_counterparty` | read | 取引先情報参照 |
| `get_settlement_instructions` | read | 登録済み SSI 取得 |
| `get_triage_history` | read | 過去トリアージ履歴 |
| `get_counterparty_exception_history` | read | 直近 30 日 CP 別失敗件数 |
| `get_fo_check_results` | read | FoCheck ルール結果取得 |
| `get_bo_sendback_reason` | read | BoAgent 差し戻し理由取得 |
| `create_amend_event` | **HITL write** | Amend イベント作成 |
| `create_cancel_event` | **HITL write** | Cancel イベント作成 |
| `provide_explanation` | write | 説明付き FoValidated 遷移 |
| `escalate_to_fo_user` | write | FoUserToValidate 遷移 |

### BO エージェント用ツール（`BO_ALL_TOOLS`）

| ツール名 | 種別 | 説明 |
|---------|------|------|
| `get_trade_detail` | read | 取引詳細取得 |
| `get_counterparty` | read | 取引先情報参照 |
| `get_settlement_instructions` | read | 登録済み SSI 取得 |
| `lookup_external_ssi` | read | 外部ソース SSI 検索 |
| `get_triage_history` | read | 過去トリアージ履歴 |
| `get_counterparty_exception_history` | read | 直近 30 日 CP 別失敗件数 |
| `get_bo_check_results` | read | BoCheck ルール結果取得 |
| `get_fo_explanation` | read | FoAgent 説明取得（2 回目トリアージ時） |
| `register_ssi` | **HITL write** | 新規 SSI 登録 |
| `update_ssi` | **HITL write** | 既存 SSI 修正（BIC/口座/IBAN） |
| `reactivate_counterparty` | **HITL write** | 非アクティブ CP 再有効化 |
| `send_back_to_fo` | **HITL write** | FoAgent 差し戻し（1 回目のみ） |
| `escalate_to_bo_user` | write | BoUserToValidate 遷移 |

---

## AgentState（LangGraph）

```python
class FoAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str
    error_message: str
    action_taken: bool
    triage_path: str          # 診断パス種別
    sendback_count: int       # BoAgent からの差し戻し回数
    failed_rules: list[str]
    cost_log: Annotated[list[dict], operator.add]
    total_cost_usd: Annotated[float, operator.add]
    task_type: str            # "simple" / "complex" / "critical"
    selected_model: str       # 実際に使用したモデル ID

class BoAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str
    error_message: str
    action_taken: bool
    triage_path: str          # AG01 / MISSING_SSI / BE01 / AM04 / COMPOUND / UNKNOWN
    sendback_count: int
    failed_rules: list[str]
    counterparty_lei: str
    currency: str
    cost_log: Annotated[list[dict], operator.add]
    total_cost_usd: Annotated[float, operator.add]
    task_type: str
    selected_model: str
```

---

## フロントエンド画面一覧

| 画面 | パス | 説明 |
|------|------|------|
| TriagePage | `/` | レガシートリアージ UI（旧 agent.py 使用） |
| TradeListPage | `/trades` | 取引一覧・workflow_status フィルタ |
| TradeInputPage | `/trades/new` | 新規取引入力フォーム |
| TradeDetailPage | `/trades/:id` | 取引詳細（FoCheck/BoCheck/Events/Triage タブ） |
| StpExceptionListPage | `/stp-exceptions` | STP 例外一覧・ルール違反モーダル |
| CounterpartyListPage | `/counterparties` | CP 一覧・フィルタ |
| CounterpartyEditPage | `/counterparties/:lei` | CP 編集（name/BIC/is_active） |
| SettingsPage | `/settings` | FoCheck/BoCheck トリガー設定（auto/manual） |
| RuleListPage | `/rules` | FO/BO ルール一覧（severity バッジ・stub フラグ） |
| CostPage | `/cost` | LLM コストダッシュボード（サマリー/エージェント別/日次） |
