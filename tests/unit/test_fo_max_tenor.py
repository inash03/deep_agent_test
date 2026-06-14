"""Requirement-driven unit tests for the FO maximum-settlement-tenor rule.

Pure function: only SimpleNamespace mocks are needed. No DB, LLM, or network.
Spec: docs/specs/fo-value-date.md and features/specs/fo_max_tenor.spec.feature.
"""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

from src.domain.check_rules import (
    MAX_SETTLEMENT_TENOR_DAYS,
    _value_date_within_max_tenor,
)


def _trade(days_after: int) -> SimpleNamespace:
    trade_date = date(2026, 6, 1)
    return SimpleNamespace(
        trade_date=trade_date,
        value_date=trade_date + timedelta(days=days_after),
    )


def test_max_settlement_tenor_days_is_730() -> None:
    assert MAX_SETTLEMENT_TENOR_DAYS == 730


def test_value_date_within_max_tenor_passes() -> None:
    passed, _ = _value_date_within_max_tenor(_trade(30))
    assert passed is True


def test_value_date_at_max_tenor_boundary_passes() -> None:
    passed, _ = _value_date_within_max_tenor(_trade(MAX_SETTLEMENT_TENOR_DAYS))
    assert passed is True


def test_value_date_one_day_beyond_max_tenor_fails() -> None:
    passed, message = _value_date_within_max_tenor(_trade(MAX_SETTLEMENT_TENOR_DAYS + 1))
    assert passed is False
    assert "maximum settlement tenor" in message.lower()
