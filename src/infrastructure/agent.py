"""LangGraph ReAct agent for STP Exception Triage.

Graph topology:

  START
    │
    ▼
  [agent_node] ◄────────────────────────┐
    │                                   │
    │ route_after_agent                 │
    ├─ register_ssi tool call ──► [register_ssi_node]  ← interrupt_before here
    ├─ other tool calls ─────────► [read_tools_node]   ─┘
    └─ no tool calls ────────────► END

HITL flow:
  - Graph pauses before register_ssi_node
  - Caller checks get_state().next == ("register_ssi_node",)
  - On approval : graph.invoke(None, config)  → continues normally
  - On rejection: graph.update_state() injects a rejection ToolMessage,
                  then graph.invoke(None, config) continues to agent_node
"""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any, Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from src.infrastructure.tools import ALL_TOOLS, READ_ONLY_TOOLS, register_ssi

_logger = logging.getLogger("stp_triage.agent")

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert STP (Straight-Through Processing) exception triage agent
at a securities firm. Your job is to investigate a failed trade and diagnose
the root cause using the tools available to you.

Investigation steps (follow this order):
1. Call get_trade_detail to retrieve the trade.
2. Call get_counterparty to verify the counterparty LEI.
3. Call get_reference_data to verify the instrument.
4. Call get_settlement_instructions to check if an SSI is registered.
5. If no SSI found: call lookup_external_ssi to check the external source.
6. If external SSI found: call register_ssi to register it
   (an operator will approve before it is saved).

When you have enough information to reach a conclusion, output ONLY a JSON
object as your final message — no markdown fences, no other text:

{
  "diagnosis": "<clear explanation of root cause and findings>",
  "root_cause": "<one of: MISSING_SSI | BIC_FORMAT_ERROR | INVALID_VALUE_DATE | INSTRUMENT_NOT_FOUND | COUNTERPARTY_NOT_FOUND | UNKNOWN>",
  "recommended_action": "<what the operator should do to resolve this>"
}
"""

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str
    error_message: str
    action_taken: bool


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _route_after_agent(
    state: AgentState,
) -> Literal["read_tools", "register_ssi_node", "__end__"]:
    """Decide what to do after the LLM responds."""
    last = state["messages"][-1]
    if not isinstance(last, AIMessage) or not last.tool_calls:
        return END  # LLM is done — no more tool calls
    for tc in last.tool_calls:
        if tc["name"] == "register_ssi":
            return "register_ssi_node"  # write op → HITL interrupt
    return "read_tools"


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def build_graph() -> Any:
    """Build and compile the STP triage LangGraph.

    Returns a compiled StateGraph with:
      - MemorySaver checkpointer (enables HITL via thread_id)
      - interrupt_before=["register_ssi_node"]
    """
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.environ["ANTHROPIC_API_KEY"],
    ).bind_tools(ALL_TOOLS)

    read_tools_node = ToolNode(READ_ONLY_TOOLS)

    # ------------------------------------------------------------------
    # Node: agent
    # ------------------------------------------------------------------
    def agent_node(state: AgentState) -> dict[str, Any]:
        messages = list(state["messages"])
        # Prepend system prompt if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        _logger.info(
            "agent_node: invoking LLM",
            extra={"node": "agent", "trade_id": state.get("trade_id"), "message_count": len(messages)},
        )

        response = llm.invoke(messages)

        if response.tool_calls:
            for tc in response.tool_calls:
                _logger.info(
                    "agent_node: tool call planned",
                    extra={"node": "agent", "tool": tc["name"], "args": tc["args"]},
                )
        else:
            _logger.info(
                "agent_node: final response (no tool calls)",
                extra={"node": "agent", "trade_id": state.get("trade_id")},
            )

        return {"messages": [response]}

    # ------------------------------------------------------------------
    # Node: register_ssi_node
    # Executes the register_ssi tool call from the last AIMessage.
    # The graph is configured with interrupt_before=["register_ssi_node"],
    # so this node only runs after the operator approves.
    # ------------------------------------------------------------------
    def register_ssi_node(state: AgentState) -> dict[str, Any]:
        last = state["messages"][-1]
        tool_call = next(tc for tc in last.tool_calls if tc["name"] == "register_ssi")
        _logger.info(
            "register_ssi_node: executing SSI registration (HITL approved)",
            extra={
                "node": "register_ssi_node",
                "trade_id": state.get("trade_id"),
                "lei": tool_call["args"].get("lei"),
                "currency": tool_call["args"].get("currency"),
                "bic": tool_call["args"].get("bic"),
            },
        )
        result = register_ssi.invoke(tool_call["args"])
        _logger.info(
            "register_ssi_node: SSI registration complete",
            extra={"node": "register_ssi_node", "trade_id": state.get("trade_id")},
        )
        return {
            "messages": [ToolMessage(content=result, tool_call_id=tool_call["id"])],
            "action_taken": True,
        }

    # ------------------------------------------------------------------
    # Assemble graph
    # ------------------------------------------------------------------
    builder = StateGraph(AgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("read_tools", read_tools_node)
    builder.add_node("register_ssi_node", register_ssi_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        _route_after_agent,
        {
            "read_tools": "read_tools",
            "register_ssi_node": "register_ssi_node",
            END: END,
        },
    )
    builder.add_edge("read_tools", "agent")
    builder.add_edge("register_ssi_node", "agent")

    return builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["register_ssi_node"],
    )
