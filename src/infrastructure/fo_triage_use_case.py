"""FoTriageUseCase — orchestrates the FoAgent LangGraph for FO STP triage.

Two-phase execution:
  Phase 1 — start():
    Launches the FoAgent ReAct loop. If the agent calls a HITL tool
    (create_amend_event, create_cancel_event), the graph pauses
    (interrupt_before). Returns PENDING_APPROVAL with run_id.
    Otherwise returns COMPLETED with the full diagnosis.

  Phase 2 — resume():
    Resumes a paused run after the operator approves or rejects.
    Approval  → graph executes the HITL node, then continues to diagnosis.
    Rejection → injects a rejection ToolMessage, graph continues to diagnosis.
"""

from __future__ import annotations

import json
import logging
import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from src.domain.entities import RootCause, Step, TriageResult, TriageStatus
from src.infrastructure.fo_agent import _FO_HITL_TOOL_TO_NODE, build_fo_graph

_FO_HITL_TOOL_NAMES: frozenset[str] = frozenset(_FO_HITL_TOOL_TO_NODE.keys())
_FO_HITL_NODE_NAMES: frozenset[str] = frozenset(_FO_HITL_TOOL_TO_NODE.values())

_logger = logging.getLogger("stp_triage.fo_use_case")


class FoTriageUseCase:
    def __init__(self) -> None:
        self._graph = build_fo_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, trade_id: str, error_context: str = "") -> TriageResult:
        """Start a new FO triage run. Returns COMPLETED or PENDING_APPROVAL."""
        run_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": run_id}}

        _logger.info(
            "fo_triage started",
            extra={"run_id": run_id, "trade_id": trade_id},
        )

        content = f"Please investigate the FoCheck failures for trade {trade_id}."
        if error_context:
            content += f"\nAdditional context: {error_context}"

        initial_state = {
            "messages": [HumanMessage(content=content)],
            "trade_id": trade_id,
            "error_message": error_context,
            "action_taken": False,
            "cost_log": [],
            "total_cost_usd": 0.0,
            "task_type": "complex",
            "selected_model": "",
        }

        self._graph.invoke(initial_state, config)
        return self._build_result(run_id, config, trade_id=trade_id)

    def resume(self, run_id: str, *, approved: bool) -> TriageResult:
        """Resume a PENDING_APPROVAL FO triage run after HITL decision."""
        config = {"configurable": {"thread_id": run_id}}

        _logger.info(
            "fo_hitl decision received",
            extra={"run_id": run_id, "approved": approved},
        )

        state_snapshot = self._graph.get_state(config)
        trade_id = state_snapshot.values.get("trade_id", "")

        if not approved:
            last_msg = state_snapshot.values["messages"][-1]
            tool_call = next(
                tc for tc in last_msg.tool_calls if tc["name"] in _FO_HITL_TOOL_NAMES
            )
            rejection_msg = ToolMessage(
                content=(
                    f"Action '{tool_call['name']}' was rejected by the operator. "
                    "Proceed to produce the final diagnosis without executing this action."
                ),
                tool_call_id=tool_call["id"],
            )
            self._graph.update_state(
                config,
                {"messages": [rejection_msg]},
                as_node=_FO_HITL_TOOL_TO_NODE[tool_call["name"]],
            )

        self._graph.invoke(None, config)
        return self._build_result(run_id, config, trade_id=trade_id, override_action_taken=approved)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_result(
        self,
        run_id: str,
        config: dict,
        *,
        trade_id: str = "",
        override_action_taken: bool | None = None,
    ) -> TriageResult:
        snapshot = self._graph.get_state(config)
        state = snapshot.values
        next_nodes = snapshot.next

        if any(n in _FO_HITL_NODE_NAMES for n in (next_nodes or ())):
            return self._pending_result(run_id, state, trade_id=trade_id)

        action_taken = (
            override_action_taken
            if override_action_taken is not None
            else state.get("action_taken", False)
        )
        return self._completed_result(run_id, state, trade_id=trade_id, action_taken=action_taken)

    def _pending_result(self, run_id: str, state: dict, *, trade_id: str) -> TriageResult:
        last_msg = state["messages"][-1]
        _logger.info(
            "fo_hitl interrupt: awaiting operator approval",
            extra={"run_id": run_id, "trade_id": trade_id},
        )
        tool_call = next(
            (tc for tc in last_msg.tool_calls if tc["name"] in _FO_HITL_TOOL_NAMES),
            None,
        )
        action_type = tool_call["name"] if tool_call else None
        description = _format_fo_hitl_action(tool_call) if tool_call else "Pending operator action"
        return TriageResult(
            trade_id=trade_id,
            status=TriageStatus.PENDING_APPROVAL,
            run_id=run_id,
            pending_action_type=action_type,
            pending_action_description=description,
            steps=_extract_steps(state["messages"]),
        )

    def _completed_result(
        self, run_id: str, state: dict, *, trade_id: str, action_taken: bool
    ) -> TriageResult:
        diagnosis, root_cause, recommended_action = _parse_llm_output(state["messages"])
        steps = _extract_steps(state["messages"])
        _logger.info(
            "fo_triage completed",
            extra={
                "run_id": run_id,
                "trade_id": trade_id,
                "root_cause": root_cause.value if root_cause else None,
                "action_taken": action_taken,
                "step_count": len(steps),
            },
        )
        return TriageResult(
            trade_id=trade_id,
            status=TriageStatus.COMPLETED,
            run_id=run_id,
            diagnosis=diagnosis,
            root_cause=root_cause,
            recommended_action=recommended_action,
            action_taken=action_taken,
            steps=steps,
        )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _parse_llm_output(messages: list[BaseMessage]) -> tuple[str, RootCause, str]:
    final_msg: AIMessage | None = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            final_msg = msg
            break

    if final_msg is None:
        return "No diagnosis produced.", RootCause.UNKNOWN, "Manual investigation required."

    try:
        content = str(final_msg.content).strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        brace_pos = content.find("{")
        if brace_pos > 0:
            content = content[brace_pos:]
        data = json.loads(content)
        diagnosis = str(data["diagnosis"])
        root_cause = RootCause(data["root_cause"])
        recommended_action = str(data["recommended_action"])
    except (json.JSONDecodeError, KeyError, ValueError):
        diagnosis = str(final_msg.content)
        root_cause = RootCause.UNKNOWN
        recommended_action = "Manual investigation required."

    return diagnosis, root_cause, recommended_action


def _extract_steps(messages: list[BaseMessage]) -> list[Step]:
    tool_results: dict[str, str] = {
        msg.tool_call_id: str(msg.content)
        for msg in messages
        if isinstance(msg, ToolMessage)
    }

    steps: list[Step] = []
    for msg in messages:
        if not isinstance(msg, AIMessage) or not msg.tool_calls:
            continue
        for tc in msg.tool_calls:
            raw_output = tool_results.get(tc["id"])
            output: dict | None = None
            if raw_output is not None:
                try:
                    output = json.loads(raw_output)
                except json.JSONDecodeError:
                    output = {"raw": raw_output}

            is_hitl = tc["name"] in _FO_HITL_TOOL_NAMES
            steps.append(
                Step(
                    step_type="hitl_prompt" if is_hitl else "tool_call",
                    name=tc["name"],
                    input=dict(tc["args"]),
                    output=output,
                )
            )

    return steps


def _format_fo_hitl_action(tool_call: dict) -> str:
    name = tool_call["name"]
    args = tool_call.get("args", {})
    if name == "create_amend_event":
        return (
            f"Amend trade '{args.get('trade_id')}': "
            f"fields={args.get('amended_fields', '{}')} — {args.get('reason', '')}"
        )
    if name == "create_cancel_event":
        return f"Cancel trade '{args.get('trade_id')}': {args.get('reason', '')}"
    return f"Pending action: {name}"
