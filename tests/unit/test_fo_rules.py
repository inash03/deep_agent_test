"""Requirement-driven unit tests for FO check rule implementations.

All rules are pure functions: only SimpleNamespace mocks are needed.
No database, LLM, or network access.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch


from src.domain.check_rules import (
    _amount_positive,
    _settlement_currency_consistency,
    _trade_date_not_weekend,
    _value_date_after_trade_date,
    _value_date_not_past,
    _value_date_settlement_cycle,
)


def _trade(**kwargs) -> SimpleNamespace:
    defaults = dict(
        trade_date=date(2026, 5, 6),  # Wednesday
        value_date=date(2026, 5, 8),  # Friday (T+2)
        input_date=date(2026, 5, 6),
        amount=Decimal("1000000"),
        instrument_id="EURUSD",
        currency="USD",
        settlement_currency="USD",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# _trade_date_not_weekend
# ---------------------------------------------------------------------------


def test_trade_date_weekday_passes() -> None:
    passed, _ = _trade_date_not_weekend(_trade(trade_date=date(2026, 5, 6)))  # Wednesday
    assert passed is True


def test_trade_date_saturday_fails() -> None:
    passed, message = _trade_date_not_weekend(_trade(trade_date=date(2026, 5, 9)))  # Saturday
    assert passed is False
    assert "Saturday" in message


def test_trade_date_sunday_fails() -> None:
    passed, message = _trade_date_not_weekend(_trade(trade_date=date(2026, 5, 10)))  # Sunday
    assert passed is False
    assert "Sunday" in message


# ---------------------------------------------------------------------------
# _value_date_after_trade_date
# ---------------------------------------------------------------------------


def test_value_date_strictly_after_trade_date_passes() -> None:
    trade = _trade(trade_date=date(2026, 5, 6), value_date=date(2026, 5, 8))
    passed, _ = _value_date_after_trade_date(trade)
    assert passed is True


def test_value_date_equal_to_trade_date_fails() -> None:
    trade = _trade(trade_date=date(2026, 5, 6), value_date=date(2026, 5, 6))
    passed, message = _value_date_after_trade_date(trade)
    assert passed is False
    assert "strictly after" in message


def test_value_date_before_trade_date_fails() -> None:
    trade = _trade(trade_date=date(2026, 5, 6), value_date=date(2026, 5, 5))
    passed, _ = _value_date_after_trade_date(trade)
    assert passed is False


# ---------------------------------------------------------------------------
# _value_date_not_past
# ---------------------------------------------------------------------------


def test_value_date_today_passes() -> None:
    today = date(2026, 5, 14)
    with patch("src.domain.check_rules.date") as mock_date:
        mock_date.today.return_value = today
        passed, _ = _value_date_not_past(_trade(value_date=today))
    assert passed is True


def test_value_date_in_future_passes() -> None:
    today = date(2026, 5, 14)
    with patch("src.domain.check_rules.date") as mock_date:
        mock_date.today.return_value = today
        passed, _ = _value_date_not_past(_trade(value_date=date(2026, 5, 20)))
    assert passed is True


def test_value_date_in_past_fails() -> None:
    today = date(2026, 5, 14)
    with patch("src.domain.check_rules.date") as mock_date:
        mock_date.today.return_value = today
        passed, message = _value_date_not_past(_trade(value_date=date(2026, 5, 1)))
    assert passed is False
    assert "past" in message


# ---------------------------------------------------------------------------
# _value_date_settlement_cycle
# ---------------------------------------------------------------------------


def test_value_date_exactly_t_plus_2_passes() -> None:
    trade_date = date(2026, 5, 6)
    passed, _ = _value_date_settlement_cycle(
        _trade(trade_date=trade_date, value_date=trade_date + timedelta(days=2))
    )
    assert passed is True


def test_value_date_beyond_t_plus_2_passes() -> None:
    trade_date = date(2026, 5, 6)
    passed, _ = _value_date_settlement_cycle(
        _trade(trade_date=trade_date, value_date=trade_date + timedelta(days=5))
    )
    assert passed is True


def test_value_date_t_plus_1_fails_settlement_cycle() -> None:
    trade_date = date(2026, 5, 6)
    passed, message = _value_date_settlement_cycle(
        _trade(trade_date=trade_date, value_date=trade_date + timedelta(days=1))
    )
    assert passed is False
    assert "T+2" in message


# ---------------------------------------------------------------------------
# _amount_positive
# ---------------------------------------------------------------------------


def test_positive_amount_passes() -> None:
    passed, _ = _amount_positive(_trade(amount=Decimal("1000000")))
    assert passed is True


def test_zero_amount_fails() -> None:
    # Pydantic prevents zero at the API boundary; this rule guards the domain layer.
    passed, message = _amount_positive(_trade(amount=Decimal("0")))
    assert passed is False
    assert "greater than zero" in message


def test_negative_amount_fails() -> None:
    passed, _ = _amount_positive(_trade(amount=Decimal("-500")))
    assert passed is False


# ---------------------------------------------------------------------------
# _settlement_currency_consistency
# ---------------------------------------------------------------------------


def test_settlement_currency_as_quote_passes() -> None:
    trade = _trade(instrument_id="EURUSD", settlement_currency="USD")
    passed, _ = _settlement_currency_consistency(trade)
    assert passed is True


def test_settlement_currency_as_base_passes() -> None:
    trade = _trade(instrument_id="EURUSD", settlement_currency="EUR")
    passed, _ = _settlement_currency_consistency(trade)
    assert passed is True


def test_settlement_currency_absent_from_instrument_fails() -> None:
    trade = _trade(instrument_id="EURUSD", settlement_currency="JPY")
    passed, message = _settlement_currency_consistency(trade)
    assert passed is False
    assert "JPY" in message
    assert "EURUSD" in message
