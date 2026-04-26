"""Cost tracking utilities for LangGraph agent LLM calls.

Provides model pricing, cost calculation, audit log building, model selection,
and a wrapper that combines LLM invocation with cost capture.
"""

from __future__ import annotations

import operator
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Model constants
# ---------------------------------------------------------------------------

MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# Cost threshold: if total_cost_usd exceeds this, force Haiku
COST_THRESHOLD_USD = 0.10

# ---------------------------------------------------------------------------
# Pricing table  (USD per 1M tokens)
# Note: Opus is listed for reference only — this system does not use it.
# ---------------------------------------------------------------------------

_PRICE_TABLE: dict[str, dict[str, float]] = {
    MODEL_HAIKU: {"input_per_1m": 0.80, "output_per_1m": 4.00},
    MODEL_SONNET: {"input_per_1m": 3.00, "output_per_1m": 15.00},
}

_DEFAULT_PRICES = _PRICE_TABLE[MODEL_SONNET]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calc_cost(model: str, usage_metadata: dict[str, Any]) -> float:
    """Return cost in USD for a single LLM call given token usage."""
    prices = _PRICE_TABLE.get(model, _DEFAULT_PRICES)
    input_tokens: int = usage_metadata.get("input_tokens", 0)
    output_tokens: int = usage_metadata.get("output_tokens", 0)
    cost = (
        input_tokens * prices["input_per_1m"] + output_tokens * prices["output_per_1m"]
    ) / 1_000_000
    return round(cost, 8)


def build_cost_log(node: str, model: str, response: Any, reason: str) -> dict:
    """Build an audit log entry for one LLM call.

    Captures node name, model, token counts, cost, decision reason, and
    timestamp.  Stored in AgentState.cost_log for regulatory audit trails.
    """
    usage: dict[str, Any] = {}
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        usage = dict(response.usage_metadata)
    cost = calc_cost(model, usage)
    return {
        "node": node,
        "model": model,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cost_usd": cost,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def select_model(task_type: str, total_cost_usd: float) -> tuple[str, str]:
    """Choose the appropriate model and return (model_id, reason).

    Rules:
    - cost > COST_THRESHOLD_USD → Haiku (cost guard, regardless of task_type)
    - task_type == "simple"     → Haiku
    - task_type == "complex"    → Sonnet
    - task_type == "critical"   → Sonnet  (Opus excluded per system policy)
    """
    if total_cost_usd > COST_THRESHOLD_USD:
        return (
            MODEL_HAIKU,
            f"cost_threshold_exceeded: ${total_cost_usd:.4f} > ${COST_THRESHOLD_USD}",
        )
    if task_type == "simple":
        return MODEL_HAIKU, "task_type=simple"
    # "complex" and "critical" → Sonnet (Opus not used in this demo system)
    return MODEL_SONNET, f"task_type={task_type}"


def call_with_cost_tracking(
    llm: Any,
    messages: list,
    node_name: str,
    model: str,
    reason: str = "",
) -> tuple[Any, dict, float]:
    """Invoke *llm* with *messages* and return (response, cost_log_entry, cost_usd).

    Drop-in replacement for ``llm.invoke(messages)`` that also captures cost
    information suitable for storing in AgentState.
    """
    response = llm.invoke(messages)
    log_entry = build_cost_log(node_name, model, response, reason)
    return response, log_entry, log_entry["cost_usd"]
