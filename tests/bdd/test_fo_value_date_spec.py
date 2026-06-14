"""Step definitions for features/specs/fo_value_date.spec.feature.

These bind the SDD detailed-scenario specification to the real Front Office
value-date rules in ``src.domain.check_rules``. The rules are pure functions,
so the scenarios are deterministic (no LLM, DB, or network).
"""

from datetime import date
from types import SimpleNamespace

from pytest_bdd import given, parsers, scenarios, then, when

from src.domain.check_rules import (
    _value_date_after_trade_date,
    _value_date_settlement_cycle,
)

scenarios("../../features/specs/fo_value_date.spec.feature")


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


@then(parsers.parse('the rule result is "{outcome}"'))
def _rule_result(result: tuple[bool, str], outcome: str) -> None:
    passed, _ = result
    expected = {"pass": True, "fail": False}[outcome]
    assert passed is expected
