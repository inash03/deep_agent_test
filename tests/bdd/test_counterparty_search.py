"""Step definitions for features/counterparty_search.feature.

These bind the BDD scenarios to the real counterparty search filter
(``CounterpartyRepository.list``), which matches a case-insensitive substring
against both the counterparty name and its LEI. Per issue #61 the search modal
reuses the existing ``GET /api/v1/counterparties`` filtering; a single search
term is matched against the name OR the LEI, which is how the modal composes the
existing name/lei filters.

Following the harness rules in docs/testing.md, no Neon/network is involved:
only the ``counterparties`` table is created on an in-memory SQLite engine, and
each scenario gets a fresh, isolated session (transaction-scoped fixture). The
repository uses ``ilike('%term%')``, which SQLite renders as a case-insensitive
``lower(...) LIKE lower(...)`` comparison over the ASCII test data.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.infrastructure.db.counterparty_repository import CounterpartyRepository
from src.infrastructure.db.models import CounterpartyModel

scenarios("../../features/counterparty_search.feature")


@pytest.fixture
def db() -> Iterator[Session]:
    """A fresh in-memory SQLite session with only the counterparties table."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    CounterpartyModel.__table__.create(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@given("the counterparty master contains:")
def _seed(db: Session, datatable: list[list[str]]) -> None:
    header, *rows = datatable
    for row in rows:
        record = dict(zip(header, row, strict=True))
        db.add(
            CounterpartyModel(
                lei=record["lei"],
                name=record["name"],
                bic="TESTBIC0",  # required, irrelevant to search
            )
        )
    db.commit()


@when(
    parsers.parse('the operator searches counterparties for "{term}"'),
    target_fixture="results",
)
def _search(db: Session, term: str) -> list[CounterpartyModel]:
    """Search the term against name OR LEI, as the modal does."""
    repo = CounterpartyRepository(db)
    by_name, _ = repo.list(name=term, limit=100)
    by_lei, _ = repo.list(lei=term, limit=100)
    merged: dict[str, CounterpartyModel] = {r.lei: r for r in (*by_name, *by_lei)}
    return list(merged.values())


@when("the operator selects the first result", target_fixture="selection")
def _select_first(results: list[CounterpartyModel]) -> CounterpartyModel:
    assert results, "expected at least one result to select"
    return results[0]


@then(parsers.parse('the results include the counterparty named "{name}"'))
def _includes(results: list[CounterpartyModel], name: str) -> None:
    assert any(r.name == name for r in results), (
        f"{name!r} not in {[r.name for r in results]}"
    )


@then("no counterparties are returned")
def _empty(results: list[CounterpartyModel]) -> None:
    assert results == []


@then(parsers.parse('the selection shows LEI "{lei}" and name "{name}"'))
def _selection_shows(selection: CounterpartyModel, lei: str, name: str) -> None:
    assert selection.lei == lei
    assert selection.name == name
