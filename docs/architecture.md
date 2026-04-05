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

### HITLフロー

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant LangGraph
    participant Operator

    Client->>FastAPI: POST /api/v1/triage
    FastAPI->>LangGraph: graph.invoke(initial_state)
    LangGraph->>LangGraph: ReAct loop (read tools)
    LangGraph->>LangGraph: LLM calls register_ssi
    Note over LangGraph: ⏸ interrupt_before=register_ssi_node
    LangGraph-->>FastAPI: snapshot.next = ("register_ssi_node",)
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
    FastAPI-->>Client: 200 COMPLETED + diagnosis
```

---

## Clean Architecture — 層構成

```mermaid
graph TB
    subgraph Presentation["Presentation Layer (src/presentation/)"]
        router["router.py\nFastAPI routers\nPOST /api/v1/triage\nPOST /api/v1/triage/{run_id}/resume"]
        schemas["schemas.py\nTriageRequest / ResumeRequest\nTriageResponse / StepOut"]
    end

    subgraph Domain["Domain Layer (src/domain/)"]
        entities["entities.py\nSTPFailure, TriageResult, Step\nRootCause enum, TriageStatus enum"]
        interfaces["interfaces.py\nITriageUseCase (abstract)\nstart() / resume()"]
    end

    subgraph Infrastructure["Infrastructure Layer (src/infrastructure/)"]
        agent["agent.py\nLangGraph StateGraph\nagent_node / read_tools_node\nregister_ssi_node"]
        tools["tools.py\nLangChain @tool functions\n6 tools (5 read + 1 write)"]
        mock["mock_store.py\nIn-memory data\n5 test scenarios"]
        usecase["triage_use_case.py\nTriageSTPFailureUseCase\nimplements ITriageUseCase"]
        logging["logging_config.py\nStructured JSON logging"]
    end

    router --> schemas
    router --> interfaces
    usecase --> interfaces
    usecase --> agent
    agent --> tools
    tools --> mock

    style Domain fill:#e8f4f8,stroke:#2980b9
    style Presentation fill:#eafaf1,stroke:#27ae60
    style Infrastructure fill:#fef9e7,stroke:#f39c12
```

**層のルール:**
- Presentation → Domain のみ参照可（Infrastructureを直接参照しない）
- Infrastructure → Domain のみ参照可
- Domain はフレームワーク依存ゼロ（純粋なPython）

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

## AgentState (LangGraph)

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # メッセージ履歴
    trade_id: str        # 調査対象トレードID
    error_message: str   # STPエラーメッセージ
    action_taken: bool   # SSI登録が実行されたか
```
