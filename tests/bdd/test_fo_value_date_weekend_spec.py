"""Step definitions for features/specs/fo_value_date_weekend.spec.feature.

Binds the SDD detailed-scenario specification to the real Front Office
value-date weekend rule in ``src.domain.check_rules``. The rule is a pure
function, so the scenarios are deterministic (no LLM, DB, or network).
"""

from datetime import date
from types import SimpleNamespace

from pytest_bdd import given, parsers, scenarios, then, when

from src.domain.check_rules import _value_date_not_weekend

scenarios("../../features/specs/fo_value_date_weekend.spec.feature")


@given(parsers.parse('a trade with trade date "{trade_date}"'), target_fixture="trade")
def _trade(trade_date: str) -> SimpleNamespace:
    return SimpleNamespace(trade_date=date.fromisoformat(trade_date))


@given(parsers.parse('a value date of "{value_date}"'))
def _value_date(trade: SimpleNamespace, value_date: str) -> None:
    trade.value_date = date.fromisoformat(value_date)


@when("the value-date-not-weekend rule runs", target_fixture="result")
def _run_value_date_not_weekend(trade: SimpleNamespace) -> tuple[bool, str]:
    return _value_date_not_weekend(trade)


@then(parsers.parse('the rule result is "{outcome}"'))
def _rule_result(result: tuple[bool, str], outcome: str) -> None:
    passed, _ = result
    expected = {"pass": True, "fail": False}[outcome]
    assert passed is expected


@then("the rule fails")
def _rule_fails(result: tuple[bool, str]) -> None:
    passed, _ = result
    assert passed is False


@then(parsers.parse('the failure message mentions "{fragment}"'))
def _message_mentions(result: tuple[bool, str], fragment: str) -> None:
    _, message = result
    assert fragment in message
