"""Step definitions for features/fo_value_date_validation.feature.

These bind the BDD scenarios to the real Front Office value-date rules in
``src.domain.check_rules``. Following the harness rules in docs/testing.md, the
rules under test are pure functions, so no LLM, DB, or network is involved.
"""

from datetime import date
from types import SimpleNamespace

from pytest_bdd import given, parsers, scenarios, then, when

from src.domain.check_rules import (
    _value_date_after_trade_date,
    _value_date_settlement_cycle,
)

scenarios("../../features/fo_value_date_validation.feature")


@given(parsers.parse('a trade with trade date "{trade_date}"'), target_fixture="trade")
def _trade(trade_date: str) -> SimpleNamespace:
    return SimpleNamespace(trade_date=date.fromisoformat(trade_date))


@given(parsers.parse('a value date of "{value_date}"'))
def _value_date(trade: SimpleNamespace, value_date: str) -> None:
    trade.value_date = date.fromisoformat(value_date)


@when("the value-date-after-trade-date rule runs", target_fixture="result")
def _run_after_trade_date(trade: SimpleNamespace) -> tuple[bool, str]:
    return _value_date_after_trade_date(trade)


@when("the settlement cycle rule runs", target_fixture="result")
def _run_settlement_cycle(trade: SimpleNamespace) -> tuple[bool, str]:
    return _value_date_settlement_cycle(trade)


@then("the rule fails")
def _rule_fails(result: tuple[bool, str]) -> None:
    passed, _ = result
    assert passed is False


@then("the rule passes")
def _rule_passes(result: tuple[bool, str]) -> None:
    passed, _ = result
    assert passed is True


@then(parsers.parse('the failure message mentions "{fragment}"'))
def _message_mentions(result: tuple[bool, str], fragment: str) -> None:
    _, message = result
    assert fragment in message
