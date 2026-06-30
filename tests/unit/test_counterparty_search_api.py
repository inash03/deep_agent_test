"""API-contract tests for counterparty search (Issue #61, FR-02).

These lock the SDD contract for the search modal at the HTTP boundary:
``docs/specs/counterparty-search.md`` (matching semantics + error mapping) and
``features/specs/counterparty_search.spec.feature``. The repository-level
substring/case-insensitive behavior is already exercised in
``tests/bdd/test_counterparty_search_spec.py``; here we prove the public
``GET /api/v1/counterparties`` endpoint wires the ``name``/``lei`` query params
through and validates ``limit``/``offset`` per the spec's error-mapping table.

Per docs/testing.md the default suite never touches a real database, so the
router's ``get_db`` dependency is overridden with an in-memory SQLite session
(``ilike`` maps to a case-insensitive ``LIKE`` on SQLite, matching the Postgres
behavior the production query relies on). Only the counterparties router is
mounted so importing the full ``src.main`` app (secrets/logging side effects)
is avoided.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.infrastructure.db.models import CounterpartyModel
from src.infrastructure.db.session import get_db
from src.presentation.routers.counterparties import router as counterparties_router

# Master mirrors features/specs/counterparty_search.spec.feature Background.
_MASTER = [
    ("213800QILIUD4ROSUO03", "Acme Bank Ltd"),
    ("5493001KJTIIGC8Y1R12", "Global Securities Inc"),
    ("9695005MSX1OYEMGDF46", "Pacific Bank Corp"),
]


@pytest.fixture
def client() -> TestClient:
    """TestClient for an app exposing only the counterparties router (fake DB)."""
    # StaticPool + check_same_thread=False: TestClient serves requests on a
    # worker thread, so the single in-memory connection must be shareable.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    CounterpartyModel.__table__.create(engine)
    with Session(engine) as db:
        for lei, name in _MASTER:
            db.add(CounterpartyModel(lei=lei, name=name, bic="TESTBIC0XXX", is_active=True))
        db.commit()

        app = FastAPI()
        app.include_router(counterparties_router)
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)


def _names(payload: dict) -> list[str]:
    return [item["name"] for item in payload["items"]]


# --- Matching semantics through the HTTP boundary --------------------------

@pytest.mark.parametrize(
    "term, expected",
    [
        ("acme", ["Acme Bank Ltd"]),                      # lowercase term, mixed data
        ("ACME", ["Acme Bank Ltd"]),                      # uppercase term, mixed data
        ("bank", ["Acme Bank Ltd", "Pacific Bank Corp"]),  # middle substring, name-asc
        ("zzz", []),                                       # no match
    ],
)
def test_name_filter_is_substring_case_insensitive(client, term, expected):
    res = client.get("/api/v1/counterparties", params={"name": term})
    assert res.status_code == 200
    assert _names(res.json()) == expected


@pytest.mark.parametrize(
    "term, expected",
    [
        ("qiliud", ["Acme Bank Ltd"]),     # middle substring, lower term
        ("QILIUD", ["Acme Bank Ltd"]),     # middle substring, upper term
        ("gdf46", ["Pacific Bank Corp"]),  # suffix of the LEI
        ("0000", []),                      # no match
    ],
)
def test_lei_filter_is_substring_case_insensitive(client, term, expected):
    res = client.get("/api/v1/counterparties", params={"lei": term})
    assert res.status_code == 200
    assert _names(res.json()) == expected


def test_name_and_lei_filters_combine_with_and(client):
    res = client.get("/api/v1/counterparties", params={"name": "bank", "lei": "213800"})
    assert res.status_code == 200
    assert _names(res.json()) == ["Acme Bank Ltd"]


def test_empty_result_is_200_not_404(client):
    res = client.get("/api/v1/counterparties", params={"name": "bank", "lei": "5493"})
    assert res.status_code == 200
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_limit_caps_page_while_total_counts_all_matches(client):
    res = client.get("/api/v1/counterparties", params={"name": "bank", "limit": 1})
    assert res.status_code == 200
    body = res.json()
    assert _names(body) == ["Acme Bank Ltd"]
    assert body["total"] == 2


# --- Error mapping (FastAPI query validation -> 422) -----------------------

@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_out_of_range_pagination_is_422(client, params):
    res = client.get("/api/v1/counterparties", params=params)
    assert res.status_code == 422
