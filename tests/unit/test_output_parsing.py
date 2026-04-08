"""Unit tests for triage_use_case helper functions.

Tests _parse_llm_output and _extract_steps without any LLM or graph invocation.
"""

import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.domain.entities import RootCause
from src.infrastructure.triage_use_case import _extract_steps, _parse_llm_output


# ---------------------------------------------------------------------------
# _parse_llm_output
# ---------------------------------------------------------------------------


class TestParseLLMOutput:
    def _make_messages(self, content: str) -> list:
        """Build a minimal message list ending with a plain AIMessage."""
        return [
            HumanMessage(content="Investigate TRD-001"),
            AIMessage(content=content),
        ]

    def test_valid_json(self):
        payload = json.dumps({
            "diagnosis": "SSI was not registered.",
            "root_cause": "MISSING_SSI",
            "recommended_action": "Register the SSI.",
        })
        diagnosis, root_cause, action = _parse_llm_output(self._make_messages(payload))

        assert diagnosis == "SSI was not registered."
        assert root_cause == RootCause.MISSING_SSI
        assert action == "Register the SSI."

    def test_json_with_markdown_fence(self):
        payload = (
            "```json\n"
            + json.dumps({
                "diagnosis": "BIC format is wrong.",
                "root_cause": "BIC_FORMAT_ERROR",
                "recommended_action": "Correct the BIC.",
            })
            + "\n```"
        )
        _, root_cause, _ = _parse_llm_output(self._make_messages(payload))
        assert root_cause == RootCause.BIC_FORMAT_ERROR

    def test_invalid_json_falls_back_to_unknown(self):
        diagnosis, root_cause, _ = _parse_llm_output(
            self._make_messages("I could not determine the root cause.")
        )
        assert root_cause == RootCause.UNKNOWN
        assert "could not determine" in diagnosis

    def test_no_final_ai_message_falls_back(self):
        # Only a HumanMessage — no AIMessage without tool_calls
        messages = [HumanMessage(content="Investigate")]
        diagnosis, root_cause, _ = _parse_llm_output(messages)
        assert root_cause == RootCause.UNKNOWN

    def test_skips_ai_messages_with_tool_calls(self):
        """The function must skip AIMessages that still have pending tool_calls."""
        tool_call_msg = AIMessage(
            content="",
            tool_calls=[{"id": "tc1", "name": "get_trade_detail", "args": {"trade_id": "TRD-001"}}],
        )
        final_msg = AIMessage(
            content=json.dumps({
                "diagnosis": "Instrument not found.",
                "root_cause": "INSTRUMENT_NOT_FOUND",
                "recommended_action": "Add instrument to reference data.",
            })
        )
        _, root_cause, _ = _parse_llm_output([tool_call_msg, final_msg])
        assert root_cause == RootCause.INSTRUMENT_NOT_FOUND


# ---------------------------------------------------------------------------
# _extract_steps
# ---------------------------------------------------------------------------


class TestExtractSteps:
    def _make_tool_call_msg(self, tool_name: str, args: dict, call_id: str) -> AIMessage:
        return AIMessage(
            content="",
            tool_calls=[{"id": call_id, "name": tool_name, "args": args}],
        )

    def _make_tool_result_msg(self, content: dict, call_id: str) -> ToolMessage:
        return ToolMessage(content=json.dumps(content), tool_call_id=call_id)

    def test_single_tool_call_with_result(self):
        messages = [
            HumanMessage(content="Investigate TRD-001"),
            self._make_tool_call_msg("get_trade_detail", {"trade_id": "TRD-001"}, "tc1"),
            self._make_tool_result_msg({"trade_id": "TRD-001", "currency": "USD"}, "tc1"),
        ]
        steps = _extract_steps(messages)

        assert len(steps) == 1
        assert steps[0].name == "get_trade_detail"
        assert steps[0].step_type == "tool_call"
        assert steps[0].input == {"trade_id": "TRD-001"}
        assert steps[0].output == {"trade_id": "TRD-001", "currency": "USD"}

    def test_multiple_tool_calls(self):
        messages = [
            HumanMessage(content="Investigate TRD-001"),
            self._make_tool_call_msg("get_trade_detail", {"trade_id": "TRD-001"}, "tc1"),
            self._make_tool_result_msg({"trade_id": "TRD-001"}, "tc1"),
            self._make_tool_call_msg("get_counterparty", {"lei": "213800QILIUD4ROSUO03"}, "tc2"),
            self._make_tool_result_msg({"found": True, "name": "Acme Bank"}, "tc2"),
        ]
        steps = _extract_steps(messages)

        assert len(steps) == 2
        assert steps[0].name == "get_trade_detail"
        assert steps[1].name == "get_counterparty"

    def test_register_ssi_step_type_is_hitl_prompt(self):
        messages = [
            self._make_tool_call_msg(
                "register_ssi",
                {"lei": "213800QILIUD4ROSUO03", "currency": "USD", "bic": "ACMEGB2L", "account": "GB29"},
                "tc1",
            ),
            self._make_tool_result_msg({"success": True}, "tc1"),
        ]
        steps = _extract_steps(messages)

        assert steps[0].step_type == "hitl_prompt"
        assert steps[0].name == "register_ssi"

    def test_no_tool_calls_returns_empty(self):
        messages = [
            HumanMessage(content="Investigate"),
            AIMessage(content='{"diagnosis": "done", "root_cause": "UNKNOWN", "recommended_action": "none"}'),
        ]
        steps = _extract_steps(messages)
        assert steps == []

    def test_tool_call_without_result_has_none_output(self):
        """Tool call pending (no ToolMessage yet) → output is None."""
        messages = [
            self._make_tool_call_msg("get_trade_detail", {"trade_id": "TRD-001"}, "tc1"),
            # no ToolMessage
        ]
        steps = _extract_steps(messages)
        assert steps[0].output is None
