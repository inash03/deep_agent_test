"""BoTriageUseCase — orchestrates the BoAgent LangGraph for BO STP triage.

Two-phase execution:
  Phase 1 — start():
    Launches the BoAgent ReAct loop. If the agent calls a HITL tool
    (register_ssi, reactivate_counterparty, update_ssi, send_back_to_fo),
    the graph pauses (interrupt_before). Returns PENDING_APPROVAL with run_id.
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
from src.infrastructure.bo_agent import (
    _BO_ALL_HITL_NODE_NAMES,
    _BO_HITL_TOOL_TO_NODE,
    build_bo_graph,
)

_BO_HITL_TOOL_NAMES: frozenset[str] = frozenset(_BO_HITL_TOOL_TO_NODE.keys())
# Include all HITL tool names (both deterministic and deep-investigation variants)
_BO_HITL_TOOL_NAMES_ALL: frozenset[str] = frozenset(
    list(_BO_HITL_TOOL_TO_NODE.keys()) +
    ["reactivate_counterparty", "register_ssi", "send_back_to_fo"]
)

_logger = logging.getLogger("stp_triage.bo_use_case")


class BoTriageUseCase:
    def __init__(self) -> None:
        self._graph = build_bo_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, trade_id: str, error_context: str = "") -> TriageResult:
        """Start a new BO triage run. Returns COMPLETED or PENDING_APPROVAL."""
        run_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": run_id}}

        _logger.info(
            "bo_triage started",
            extra={"run_id": run_id, "trade_id": trade_id},
        )

        content = f"Please investigate the BoCheck failures for trade {trade_id}."
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
        """Resume a PENDING_APPROVAL BO triage run after HITL decision."""
        config = {"configurable": {"thread_id": run_id}}

        _logger.info(
            "bo_hitl decision received",
            extra={"run_id": run_id, "approved": approved},
        )

        state_snapshot = self._graph.get_state(config)
        trade_id = state_snapshot.values.get("trade_id", "")

        if not approved:
            last_msg = state_snapshot.values["messages"][-1]
            tool_call = next(
                tc for tc in last_msg.tool_calls if tc["name"] in _BO_HITL_TOOL_NAMES_ALL
            )
            rejection_msg = ToolMessage(
                content=(
                    f"Action '{tool_call['name']}' was rejected by the operator. "
                    "Proceed to produce the final diagnosis without executing this action."
                ),
                tool_call_id=tool_call["id"],
            )
            # Use snapshot.next[0] directly so both deterministic and deep-investigation
            # HITL node variants are handled correctly without a separate lookup dict.
            self._graph.update_state(
                config,
                {"messages": [rejection_msg]},
                as_node=state_snapshot.next[0],
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

        if any(n in _BO_ALL_HITL_NODE_NAMES for n in (next_nodes or ())):
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
            "bo_hitl interrupt: awaiting operator approval",
            extra={"run_id": run_id, "trade_id": trade_id},
        )
        tool_call = next(
            (tc for tc in last_msg.tool_calls if tc["name"] in _BO_HITL_TOOL_NAMES_ALL),
            None,
        )
        action_type = tool_call["name"] if tool_call else None
        description = _format_bo_hitl_action(tool_call) if tool_call else "Pending operator action"
        return TriageResult(
            trade_id=trade_id,
            status=TriageStatus.PENDING_APPROVAL,
            run_id=run_id,
            pending_action_type=action_type,
            pending_action_description=description,
            steps=_extract_steps(state["messages"]),
            cost_log=list(state.get("cost_log") or []),
            total_cost_usd=float(state.get("total_cost_usd") or 0.0),
        )

    def _completed_result(
        self, run_id: str, state: dict, *, trade_id: str, action_taken: bool
    ) -> TriageResult:
        diagnosis, root_cause, recommended_action = _parse_llm_output(state["messages"])
        steps = _extract_steps(state["messages"])
        _logger.info(
            "bo_triage completed",
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
            cost_log=list(state.get("cost_log") or []),
            total_cost_usd=float(state.get("total_cost_usd") or 0.0),
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

            is_hitl = tc["name"] in _BO_HITL_TOOL_NAMES_ALL
            steps.append(
                Step(
                    step_type="hitl_prompt" if is_hitl else "tool_call",
                    name=tc["name"],
                    input=dict(tc["args"]),
                    output=output,
                )
            )

    return steps


def _format_bo_hitl_action(tool_call: dict) -> str:
    name = tool_call["name"]
    args = tool_call.get("args", {})
    if name == "register_ssi":
        return (
            f"Register SSI for LEI '{args.get('lei')}' / currency '{args.get('currency')}': "
            f"BIC={args.get('bic')}, account={args.get('account')}"
        )
    if name == "reactivate_counterparty":
        return f"Reactivate counterparty LEI '{args.get('lei')}' (set is_active = True)"
    if name == "update_ssi":
        parts = [f"LEI '{args.get('lei')}' / currency '{args.get('currency')}'"]
        if args.get("bic"):
            parts.append(f"BIC={args['bic']}")
        if args.get("account"):
            parts.append(f"account={args['account']}")
        if args.get("iban"):
            parts.append(f"iban={args['iban']}")
        return "Update SSI — " + ", ".join(parts)
    if name == "send_back_to_fo":
        return f"Send trade '{args.get('trade_id')}' back to FO: {args.get('reason', '')}"
    return f"Pending action: {name}"
