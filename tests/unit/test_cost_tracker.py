"""Unit tests for cost_tracker utilities.

All tests are pure — no LLM calls, no network.
"""

from __future__ import annotations

import pytest

from src.infrastructure.utils.cost_tracker import (
    COST_THRESHOLD_USD,
    MODEL_HAIKU,
    MODEL_SONNET,
    build_cost_log,
    calc_cost,
    call_with_cost_tracking,
    select_model,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeResponse:
    """Minimal stand-in for a LangChain AIMessage with usage metadata."""

    def __init__(self, input_tokens: int = 0, output_tokens: int = 0):
        self.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
        self.tool_calls = []
        self.content = "ok"


class _FakeLLM:
    """Minimal LLM stub for call_with_cost_tracking tests."""

    def __init__(self, response: _FakeResponse):
        self._response = response

    def invoke(self, messages):  # noqa: ARG002
        return self._response


# ---------------------------------------------------------------------------
# calc_cost
# ---------------------------------------------------------------------------


class TestCalcCost:
    def test_sonnet_cost(self):
        usage = {"input_tokens": 1_000, "output_tokens": 200}
        cost = calc_cost(MODEL_SONNET, usage)
        # 1000 * 3.0 / 1M + 200 * 15.0 / 1M = 0.003 + 0.003 = 0.006
        expected = (1_000 * 3.0 + 200 * 15.0) / 1_000_000
        assert abs(cost - expected) < 1e-9

    def test_haiku_cost(self):
        usage = {"input_tokens": 1_000, "output_tokens": 200}
        cost = calc_cost(MODEL_HAIKU, usage)
        expected = (1_000 * 0.80 + 200 * 4.0) / 1_000_000
        assert abs(cost - expected) < 1e-9

    def test_haiku_cheaper_than_sonnet(self):
        usage = {"input_tokens": 500, "output_tokens": 100}
        assert calc_cost(MODEL_HAIKU, usage) < calc_cost(MODEL_SONNET, usage)

    def test_zero_usage_returns_zero(self):
        assert calc_cost(MODEL_SONNET, {}) == 0.0
        assert calc_cost(MODEL_HAIKU, {"input_tokens": 0, "output_tokens": 0}) == 0.0

    def test_unknown_model_falls_back_to_sonnet_pricing(self):
        usage = {"input_tokens": 1_000, "output_tokens": 0}
        cost_unknown = calc_cost("unknown-model-xyz", usage)
        cost_sonnet = calc_cost(MODEL_SONNET, usage)
        assert cost_unknown == cost_sonnet

    def test_result_is_non_negative(self):
        cost = calc_cost(MODEL_SONNET, {"input_tokens": 100, "output_tokens": 50})
        assert cost >= 0.0


# ---------------------------------------------------------------------------
# build_cost_log
# ---------------------------------------------------------------------------


class TestBuildCostLog:
    def test_required_keys_present(self):
        resp = _FakeResponse(input_tokens=100, output_tokens=50)
        log = build_cost_log("agent", MODEL_SONNET, resp, "task_type=complex")
        for key in ("node", "model", "input_tokens", "output_tokens", "cost_usd", "reason", "timestamp"):
            assert key in log, f"missing key: {key}"

    def test_values_match_inputs(self):
        resp = _FakeResponse(input_tokens=200, output_tokens=80)
        log = build_cost_log("read_tools", MODEL_HAIKU, resp, "test reason")
        assert log["node"] == "read_tools"
        assert log["model"] == MODEL_HAIKU
        assert log["input_tokens"] == 200
        assert log["output_tokens"] == 80
        assert log["reason"] == "test reason"

    def test_cost_usd_is_positive(self):
        resp = _FakeResponse(input_tokens=500, output_tokens=200)
        log = build_cost_log("agent", MODEL_SONNET, resp, "")
        assert log["cost_usd"] > 0.0

    def test_no_usage_metadata_gives_zero_cost(self):
        class _NoUsage:
            usage_metadata = None
            content = "x"

        log = build_cost_log("agent", MODEL_SONNET, _NoUsage(), "")
        assert log["cost_usd"] == 0.0
        assert log["input_tokens"] == 0

    def test_timestamp_is_iso_format(self):
        resp = _FakeResponse()
        log = build_cost_log("agent", MODEL_SONNET, resp, "")
        # Should parse without error
        from datetime import datetime
        datetime.fromisoformat(log["timestamp"])


# ---------------------------------------------------------------------------
# select_model
# ---------------------------------------------------------------------------


class TestSelectModel:
    def test_simple_selects_haiku(self):
        model, reason = select_model("simple", 0.0)
        assert model == MODEL_HAIKU
        assert "simple" in reason

    def test_complex_selects_sonnet(self):
        model, reason = select_model("complex", 0.0)
        assert model == MODEL_SONNET
        assert "complex" in reason

    def test_critical_selects_sonnet(self):
        model, reason = select_model("critical", 0.0)
        assert model == MODEL_SONNET
        assert "critical" in reason

    def test_threshold_exceeded_forces_haiku(self):
        over = COST_THRESHOLD_USD + 0.01
        model, reason = select_model("complex", over)
        assert model == MODEL_HAIKU
        assert "cost_threshold_exceeded" in reason

    def test_threshold_exactly_at_limit_does_not_force_haiku(self):
        # > threshold triggers; == does not
        model, _ = select_model("complex", COST_THRESHOLD_USD)
        assert model == MODEL_SONNET

    def test_threshold_check_overrides_task_type(self):
        # Even "critical" should downgrade when cost is over threshold
        model, reason = select_model("critical", COST_THRESHOLD_USD + 0.001)
        assert model == MODEL_HAIKU
        assert "cost_threshold_exceeded" in reason

    def test_returns_two_item_tuple(self):
        result = select_model("complex", 0.0)
        assert len(result) == 2

    def test_reason_is_non_empty_string(self):
        _, reason = select_model("simple", 0.0)
        assert isinstance(reason, str) and len(reason) > 0


# ---------------------------------------------------------------------------
# call_with_cost_tracking
# ---------------------------------------------------------------------------


class TestCallWithCostTracking:
    def test_returns_three_items(self):
        resp = _FakeResponse(input_tokens=100, output_tokens=40)
        llm = _FakeLLM(resp)
        result = call_with_cost_tracking(llm, ["msg"], "agent", MODEL_SONNET, "test")
        assert len(result) == 3

    def test_response_is_llm_output(self):
        resp = _FakeResponse(input_tokens=100, output_tokens=40)
        llm = _FakeLLM(resp)
        response, _, _ = call_with_cost_tracking(llm, ["msg"], "agent", MODEL_SONNET, "test")
        assert response is resp

    def test_log_entry_has_correct_node(self):
        resp = _FakeResponse(input_tokens=50, output_tokens=20)
        llm = _FakeLLM(resp)
        _, log_entry, _ = call_with_cost_tracking(llm, [], "my_node", MODEL_HAIKU, "reason")
        assert log_entry["node"] == "my_node"
        assert log_entry["model"] == MODEL_HAIKU

    def test_cost_matches_log_entry(self):
        resp = _FakeResponse(input_tokens=300, output_tokens=100)
        llm = _FakeLLM(resp)
        _, log_entry, cost = call_with_cost_tracking(llm, [], "agent", MODEL_SONNET, "")
        assert cost == log_entry["cost_usd"]

    def test_cost_is_positive_for_nonzero_tokens(self):
        resp = _FakeResponse(input_tokens=100, output_tokens=50)
        llm = _FakeLLM(resp)
        _, _, cost = call_with_cost_tracking(llm, [], "agent", MODEL_SONNET, "")
        assert cost > 0.0
