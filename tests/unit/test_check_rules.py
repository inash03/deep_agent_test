from datetime import date
from types import SimpleNamespace

from src.domain.check_rules import _trade_date_not_future


def test_trade_date_not_future_compares_against_input_date() -> None:
    trade = SimpleNamespace(
        trade_date=date(2026, 5, 6),
        input_date=date(2026, 5, 5),
    )

    passed, message = _trade_date_not_future(trade)

    assert passed is False
    assert "input date 2026-05-05" in message


def test_trade_date_not_future_passes_when_trade_date_is_on_input_date() -> None:
    trade = SimpleNamespace(
        trade_date=date(2026, 5, 5),
        input_date=date(2026, 5, 5),
    )

    passed, message = _trade_date_not_future(trade)

    assert passed is True
    assert "not after input date 2026-05-05" in message
