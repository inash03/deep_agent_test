"""Step definitions for features/specs/fo_max_tenor.spec.feature.

Binds the SDD detailed boundary scenarios to the real maximum-settlement-tenor
rule in ``src.domain.check_rules``. Pure function, so deterministic.

The rule is referenced via the module so this file collects cleanly while the
rule is implemented under TDD; scenarios fail at run time until it exists.
"""

from datetime import date, timedelta
from types import SimpleNamespace

from pytest_bdd import given, parsers, scenarios, then, when

from src.domain import check_rules

scenarios("../../features/specs/fo_max_tenor.spec.feature")


@given(parsers.parse('a trade with trade date "{trade_date}"'), target_fixture="trade")
def _trade(trade_date: str) -> SimpleNamespace:
    return SimpleNamespace(trade_date=date.fromisoformat(trade_date))


@given(parsers.parse("a value date {days:d} days after the trade date"))
def _value_date(trade: SimpleNamespace, days: int) -> None:
    trade.value_date = trade.trade_date + timedelta(days=days)


@when("the maximum settlement tenor check runs", target_fixture="result")
def _run(trade: SimpleNamespace) -> tuple[bool, str]:
    return check_rules._value_date_within_max_tenor(trade)


@then(parsers.parse('the rule result is "{outcome}"'))
def _rule_result(result: tuple[bool, str], outcome: str) -> None:
    passed, _ = result
    expected = {"pass": True, "fail": False}[outcome]
    assert passed is expected
