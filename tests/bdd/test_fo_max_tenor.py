"""Step definitions for features/fo_max_tenor.feature.

Binds the business scenarios to the real Front Office maximum-settlement-tenor
rule in ``src.domain.check_rules``. The rule is a pure function, so the
scenarios are deterministic (no LLM, DB, or network).

The rule is referenced via the module (not a direct import) so that this file
collects cleanly while the rule is still being implemented under TDD; the
scenarios fail at run time (red) until the function exists.
"""

from datetime import date, timedelta
from types import SimpleNamespace

from pytest_bdd import given, parsers, scenarios, then, when

from src.domain import check_rules

scenarios("../../features/fo_max_tenor.feature")


@given(parsers.parse('a trade with trade date "{trade_date}"'), target_fixture="trade")
def _trade(trade_date: str) -> SimpleNamespace:
    return SimpleNamespace(trade_date=date.fromisoformat(trade_date))


@given(parsers.parse("a value date {days:d} days after the trade date"))
def _value_date(trade: SimpleNamespace, days: int) -> None:
    trade.value_date = trade.trade_date + timedelta(days=days)


@when("the maximum settlement tenor check runs", target_fixture="result")
def _run(trade: SimpleNamespace) -> tuple[bool, str]:
    return check_rules._value_date_within_max_tenor(trade)


@then("the trade passes the check")
def _passes(result: tuple[bool, str]) -> None:
    passed, _ = result
    assert passed is True


@then("the trade is flagged for review")
def _flagged(result: tuple[bool, str]) -> None:
    passed, _ = result
    assert passed is False
