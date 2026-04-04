"""Concrete implementation of ITriageUseCase using the LangGraph agent.

Two-phase execution:
  Phase 1 — start():
    Launches the ReAct loop. If the agent decides to call register_ssi,
    the graph pauses (interrupt_before). Returns PENDING_APPROVAL with run_id.
    Otherwise returns COMPLETED with the full diagnosis.

  Phase 2 — resume():
    Resumes a paused run after the operator approves or rejects.
    Approval  → graph executes register_ssi_node, then continues to diagnosis.
    Rejection → injects a ToolMessage saying "rejected", graph continues to diagnosis.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from src.domain.entities import RootCause, Step, TriageResult, TriageStatus
from src.domain.interfaces import ITriageUseCase, STPFailure
from src.infrastructure.agent import build_graph


class TriageSTPFailureUseCase(ITriageUseCase):
    def __init__(self) -> None:
        self._graph = build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, failure: STPFailure) -> TriageResult:
        """Start a new triage run. Returns COMPLETED or PENDING_APPROVAL."""
        run_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": run_id}}

        initial_state = {
            "messages": [
                HumanMessage(
                    content=(
                        f"Please investigate the following STP failure.\n"
                        f"Trade ID: {failure.trade_id}\n"
                        f"Error message: {failure.error_message}"
                    )
                )
            ],
            "trade_id": failure.trade_id,
            "error_message": failure.error_message,
            "action_taken": False,
        }

        self._graph.invoke(initial_state, config)
        return self._build_result(run_id, config)

    def resume(self, run_id: str, *, approved: bool) -> TriageResult:
        """Resume a PENDING_APPROVAL run after HITL decision."""
        config = {"configurable": {"thread_id": run_id}}

        if not approved:
            # Inject a rejection ToolMessage so the agent can continue
            # without a dangling unanswered tool_call in the message history.
            state_snapshot = self._graph.get_state(config)
            last_msg = state_snapshot.values["messages"][-1]
            tool_call = next(
                tc for tc in last_msg.tool_calls if tc["name"] == "register_ssi"
            )
            rejection_msg = ToolMessage(
                content=(
                    "SSI registration was rejected by the operator. "
                    "Proceed to produce the final diagnosis without registering."
                ),
                tool_call_id=tool_call["id"],
            )
            # Inject the message as if register_ssi_node had returned it
            self._graph.update_state(
                config,
                {"messages": [rejection_msg]},
                as_node="register_ssi_node",
            )

        self._graph.invoke(None, config)
        return self._build_result(run_id, config, override_action_taken=approved)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_result(
        self,
        run_id: str,
        config: dict,
        override_action_taken: bool | None = None,
    ) -> TriageResult:
        snapshot = self._graph.get_state(config)
        state = snapshot.values
        next_nodes = snapshot.next

        # Still waiting for HITL approval
        if "register_ssi_node" in (next_nodes or ()):
            return self._pending_result(run_id, state)

        # Completed — parse the LLM's final JSON message
        action_taken = (
            override_action_taken
            if override_action_taken is not None
            else state.get("action_taken", False)
        )
        return self._completed_result(run_id, state, action_taken=action_taken)

    def _pending_result(self, run_id: str, state: dict) -> TriageResult:
        last_msg = state["messages"][-1]
        tool_call = next(
            (tc for tc in last_msg.tool_calls if tc["name"] == "register_ssi"),
            None,
        )
        description = (
            _format_ssi_action(tool_call["args"]) if tool_call else "Pending SSI registration"
        )
        return TriageResult(
            trade_id=state["trade_id"],
            status=TriageStatus.PENDING_APPROVAL,
            run_id=run_id,
            pending_action_description=description,
            steps=_extract_steps(state["messages"]),
        )

    def _completed_result(
        self, run_id: str, state: dict, *, action_taken: bool
    ) -> TriageResult:
        diagnosis, root_cause, recommended_action = _parse_llm_output(state["messages"])
        return TriageResult(
            trade_id=state["trade_id"],
            status=TriageStatus.COMPLETED,
            run_id=run_id,
            diagnosis=diagnosis,
            root_cause=root_cause,
            recommended_action=recommended_action,
            action_taken=action_taken,
            steps=_extract_steps(state["messages"]),
        )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _parse_llm_output(
    messages: list[BaseMessage],
) -> tuple[str, RootCause, str]:
    """Extract diagnosis, root_cause, recommended_action from the final AIMessage."""
    final_msg: AIMessage | None = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            final_msg = msg
            break

    if final_msg is None:
        return "No diagnosis produced.", RootCause.UNKNOWN, "Manual investigation required."

    try:
        content = str(final_msg.content).strip()
        # Strip markdown fences if the LLM added them despite instructions
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        diagnosis = str(data["diagnosis"])
        root_cause = RootCause(data["root_cause"])
        recommended_action = str(data["recommended_action"])
    except (json.JSONDecodeError, KeyError, ValueError):
        # Fallback: treat full content as diagnosis text
        diagnosis = str(final_msg.content)
        root_cause = RootCause.UNKNOWN
        recommended_action = "Manual investigation required."

    return diagnosis, root_cause, recommended_action


def _extract_steps(messages: list[BaseMessage]) -> list[Step]:
    """Build a Step list from the agent message history."""
    # Map tool_call_id → ToolMessage content for quick lookup
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

            is_hitl = tc["name"] == "register_ssi"
            steps.append(
                Step(
                    step_type="hitl_prompt" if is_hitl else "tool_call",
                    name=tc["name"],
                    input=dict(tc["args"]),
                    output=output,
                )
            )

    return steps


def _format_ssi_action(args: dict) -> str:
    return (
        f"Register SSI for LEI '{args.get('lei')}' / currency '{args.get('currency')}': "
        f"BIC={args.get('bic')}, account={args.get('account')}"
    )
