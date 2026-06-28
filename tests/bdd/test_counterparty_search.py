"""Step definitions for features/counterparty_search.feature.

Binds the business scenarios to the real counterparty filtering used by
``GET /api/v1/counterparties`` — ``CounterpartyRepository.list`` — so the search
semantics (match any substring of the name or LEI, case-insensitive) are
exercised against production code rather than a reimplementation.

Per docs/testing.md the default suite never touches a real database, so the
repository is backed by an in-memory SQLite engine (a transaction-scoped fake).
Only the ``counterparties`` table is created; it uses portable column types, so
no Postgres-specific features are needed and ``ilike`` maps to a case-insensitive
``LIKE``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.infrastructure.db.counterparty_repository import CounterpartyRepository
from src.infrastructure.db.models import CounterpartyModel

scenarios("../../features/counterparty_search.feature")


@pytest.fixture
def session() -> Session:
    """In-memory SQLite session with just the counterparties table (fake DB)."""
    engine = create_engine("sqlite://")
    CounterpartyModel.__table__.create(engine)
    with Session(engine) as db:
        yield db


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


@when(parsers.parse('the operator searches counterparties by name "{term}"'),
      target_fixture="results")
def _search_by_name(repo: CounterpartyRepository, term: str) -> list[CounterpartyModel]:
    items, _ = repo.list(name=term)
    return items


@when(parsers.parse('the operator searches counterparties by LEI "{term}"'),
      target_fixture="results")
def _search_by_lei(repo: CounterpartyRepository, term: str) -> list[CounterpartyModel]:
    items, _ = repo.list(lei=term)
    return items


@when("the operator selects the only result", target_fixture="selected")
def _select_only(results: list[CounterpartyModel]) -> CounterpartyModel:
    assert len(results) == 1, f"expected exactly one result, got {len(results)}"
    return results[0]


@then(parsers.parse("the search results are:"))
def _results_match(results: list[CounterpartyModel], datatable) -> None:
    header, *rows = datatable
    assert header == ["name"]
    expected = sorted(row[0] for row in rows)
    actual = sorted(item.name for item in results)
    assert actual == expected


@then("the search returns no counterparties")
def _no_results(results: list[CounterpartyModel]) -> None:
    assert results == []


@then(parsers.parse(
    'the selected counterparty has LEI "{lei}" and name "{name}"'))
def _selected_identity(selected: CounterpartyModel, lei: str, name: str) -> None:
    assert selected.lei == lei
    assert selected.name == name
