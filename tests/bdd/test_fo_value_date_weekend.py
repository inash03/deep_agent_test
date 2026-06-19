"""Step definitions for features/fo_value_date_weekend.feature.

Binds the BDD scenarios to the real Front Office value-date weekend rule in
``src.domain.check_rules``. Per docs/testing.md the rule is a pure function, so
no LLM, DB, or network is involved.
"""

from datetime import date
from types import SimpleNamespace

from pytest_bdd import given, parsers, scenarios, then, when

from src.domain.check_rules import _value_date_not_weekend

scenarios("../../features/fo_value_date_weekend.feature")


@given(parsers.parse('a trade with trade date "{trade_date}"'), target_fixture="trade")
def _trade(trade_date: str) -> SimpleNamespace:
    return SimpleNamespace(trade_date=date.fromisoformat(trade_date))


@given(parsers.parse('a value date of "{value_date}"'))
def _value_date(trade: SimpleNamespace, value_date: str) -> None:
    trade.value_date = date.fromisoformat(value_date)


@when("the value-date-not-weekend rule runs", target_fixture="result")
def _run_value_date_not_weekend(trade: SimpleNamespace) -> tuple[bool, str]:
    return _value_date_not_weekend(trade)


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
