"""Step definitions for features/specs/counterparty_search.spec.feature.

Binds the SDD detailed scenarios to the real counterparty filtering used by
``GET /api/v1/counterparties`` — ``CounterpartyRepository.list`` — so the search
contract (substring match on name or LEI, case-insensitive; AND across filters;
name-ascending order; total counts all matches) is exercised against production
code rather than a reimplementation.

Per docs/testing.md the default suite never touches a real database, so the
repository is backed by an in-memory SQLite engine (a transaction-scoped fake).
Only the ``counterparties`` table is created; ``ilike`` maps to a
case-insensitive ``LIKE`` on SQLite, matching the Postgres behavior the
production query relies on.

``parsers.re`` (not ``parsers.parse``) is used so a quoted value can be empty —
the blank-term scenario and the no-match Examples rows render ``""``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.infrastructure.db.counterparty_repository import CounterpartyRepository
from src.infrastructure.db.models import CounterpartyModel

scenarios("../../features/specs/counterparty_search.spec.feature")


@pytest.fixture
def session() -> Session:
    """In-memory SQLite session with just the counterparties table (fake DB)."""
    engine = create_engine("sqlite://")
    CounterpartyModel.__table__.create(engine)
    with Session(engine) as db:
        yield db


def _expected_names(names: str) -> list[str]:
    """Parse a comma-separated, name-ascending expectation (``""`` -> empty)."""
    return [n.strip() for n in names.split(",") if n.strip()]


@given(parsers.parse("the counterparty master contains:"), target_fixture="repo")
def _seed_master(session: Session, datatable) -> CounterpartyRepository:
    header, *rows = datatable
    for row in rows:
        record = dict(zip(header, row))
        session.add(
            CounterpartyModel(
                lei=record["lei"],
                name=record["name"],
                bic="TESTBIC0XXX",
                is_active=True,
            )
        )
    session.commit()
    return CounterpartyRepository(session)


@when(
    parsers.re(
        r'^the operator searches counterparties by name "(?P<term>[^"]*)"$'
    ),
    target_fixture="results",
)
def _search_by_name(repo: CounterpartyRepository, term: str) -> SimpleNamespace:
    items, total = repo.list(name=term)
    return SimpleNamespace(items=items, total=total)


@when(
    parsers.re(
        r'^the operator searches counterparties by LEI "(?P<term>[^"]*)"$'
    ),
    target_fixture="results",
)
def _search_by_lei(repo: CounterpartyRepository, term: str) -> SimpleNamespace:
    items, total = repo.list(lei=term)
    return SimpleNamespace(items=items, total=total)


@when(
    parsers.re(
        r'^the operator searches counterparties by name "(?P<name>[^"]*)" '
        r'and LEI "(?P<lei>[^"]*)"$'
    ),
    target_fixture="results",
)
def _search_by_name_and_lei(
    repo: CounterpartyRepository, name: str, lei: str
) -> SimpleNamespace:
    items, total = repo.list(name=name, lei=lei)
    return SimpleNamespace(items=items, total=total)


@when(
    parsers.re(
        r'^the operator searches counterparties by name "(?P<term>[^"]*)" '
        r"with limit (?P<limit>\d+)$"
    ),
    target_fixture="results",
)
def _search_by_name_with_limit(
    repo: CounterpartyRepository, term: str, limit: str
) -> SimpleNamespace:
    items, total = repo.list(name=term, limit=int(limit))
    return SimpleNamespace(items=items, total=total)


@then(
    parsers.re(r'^the search result names in order are "(?P<names>[^"]*)"$')
)
def _names_in_order(results: SimpleNamespace, names: str) -> None:
    actual = [item.name for item in results.items]
    assert actual == _expected_names(names)


@then("the search returns no counterparties")
def _no_results(results: SimpleNamespace) -> None:
    assert results.items == []


@then(parsers.parse("the total match count is {count:d}"))
def _total_match_count(results: SimpleNamespace, count: int) -> None:
    assert results.total == count
