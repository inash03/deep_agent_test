"""Requirement-driven unit tests for BO check rule implementations.

BO rules receive pre-fetched counterparty and SSI records.
All tests use SimpleNamespace mocks — no database access.
"""

from __future__ import annotations

from types import SimpleNamespace

from src.domain.check_rules import (
    _bic_format_valid,
    _counterparty_active,
    _counterparty_exists,
    _ssi_exists,
)


def _trade(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(
        counterparty_lei=kwargs.get("counterparty_lei", "254900CUSTBANK000001"),
        currency=kwargs.get("currency", "USD"),
    )


def _cp(is_active: bool = True, name: str = "Test Bank") -> SimpleNamespace:
    return SimpleNamespace(is_active=is_active, name=name, lei="254900CUSTBANK000001")


def _ssi(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(
        bic=kwargs.get("bic", "NWBKGB2L"),
        iban=kwargs.get("iban", None),
        lei="254900CUSTBANK000001",
        currency="USD",
    )


# ---------------------------------------------------------------------------
# _counterparty_exists
# ---------------------------------------------------------------------------


def test_counterparty_exists_passes_when_found() -> None:
    passed, message = _counterparty_exists(_trade(), _cp(), None)
    assert passed is True
    assert "exists" in message


def test_counterparty_exists_fails_when_cp_is_none() -> None:
    passed, message = _counterparty_exists(_trade(), None, None)
    assert passed is False
    assert "not found" in message


# ---------------------------------------------------------------------------
# _counterparty_active
# ---------------------------------------------------------------------------


def test_counterparty_active_passes_when_active() -> None:
    passed, message = _counterparty_active(_trade(), _cp(is_active=True), None)
    assert passed is True
    assert "active" in message


def test_counterparty_active_fails_when_inactive() -> None:
    passed, message = _counterparty_active(_trade(), _cp(is_active=False), None)
    assert passed is False
    assert "inactive" in message


def test_counterparty_active_fails_when_cp_not_found() -> None:
    passed, message = _counterparty_active(_trade(), None, None)
    assert passed is False
    assert "not found" in message


# ---------------------------------------------------------------------------
# _ssi_exists
# ---------------------------------------------------------------------------


def test_ssi_exists_passes_when_ssi_found() -> None:
    passed, message = _ssi_exists(_trade(), _cp(), _ssi())
    assert passed is True
    assert "found" in message


def test_ssi_exists_fails_when_ssi_is_none() -> None:
    passed, message = _ssi_exists(_trade(), _cp(), None)
    assert passed is False
    assert "No internal SSI" in message


# ---------------------------------------------------------------------------
# _bic_format_valid
# ---------------------------------------------------------------------------


def test_bic_check_skipped_when_no_ssi() -> None:
    passed, message = _bic_format_valid(_trade(), _cp(), None)
    assert passed is True
    assert "skipped" in message


def test_bic_8_chars_passes() -> None:
    passed, _ = _bic_format_valid(_trade(), _cp(), _ssi(bic="NWBKGB2L"))
    assert passed is True


def test_bic_11_chars_passes() -> None:
    passed, _ = _bic_format_valid(_trade(), _cp(), _ssi(bic="NWBKGB2LXXX"))
    assert passed is True


def test_bic_wrong_length_fails() -> None:
    passed, message = _bic_format_valid(_trade(), _cp(), _ssi(bic="NWBK"))
    assert passed is False
    assert "8 or 11" in message


def test_bic_9_chars_fails() -> None:
    passed, message = _bic_format_valid(_trade(), _cp(), _ssi(bic="NWBKGB2LX"))
    assert passed is False
    assert "8 or 11" in message
