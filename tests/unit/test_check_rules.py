from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from src.domain.check_rules import _iban_format_valid, _trade_date_not_future

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TRADE = SimpleNamespace()
_CP = None


def _ssi(iban: str | None) -> SimpleNamespace:
    return SimpleNamespace(iban=iban)


def test_trade_date_not_future_compares_against_input_date() -> None:
    trade = SimpleNamespace(
        trade_date=date(2026, 5, 6),
        input_date=date(2026, 5, 5),
    )

    passed, message = _trade_date_not_future(trade)

    assert passed is False
    assert "input date 2026-05-05" in message


def test_trade_date_not_future_passes_when_trade_date_is_on_input_date() -> None:
    trade = SimpleNamespace(
        trade_date=date(2026, 5, 5),
        input_date=date(2026, 5, 5),
    )

    passed, message = _trade_date_not_future(trade)

    assert passed is True
    assert "not after input date 2026-05-05" in message


# ---------------------------------------------------------------------------
# _iban_format_valid
# ---------------------------------------------------------------------------


def test_iban_none_skips_validation() -> None:
    passed, message = _iban_format_valid(_TRADE, _CP, _ssi(None))
    assert passed is True
    assert "No IBAN" in message


def test_ssi_none_skips_validation() -> None:
    passed, message = _iban_format_valid(_TRADE, _CP, None)
    assert passed is True


def test_iban_bad_regex_fails_before_schwifty() -> None:
    passed, message = _iban_format_valid(_TRADE, _CP, _ssi("not-an-iban"))
    assert passed is False
    assert "does not match" in message


def test_valid_iban_passes_mod97() -> None:
    # GB29NWBK60161331926819 — real valid IBAN with correct mod-97 checksum
    passed, message = _iban_format_valid(_TRADE, _CP, _ssi("GB29NWBK60161331926819"))
    assert passed is True
    assert "mod-97" in message or "valid format" in message


def test_invalid_checksum_fails_mod97() -> None:
    # GB00 has checksum 00 which is always invalid under mod-97
    passed, message = _iban_format_valid(_TRADE, _CP, _ssi("GB00NWBK60161331926819"))
    assert passed is False
    assert "checksum" in message or "validation" in message


def test_schwifty_import_error_falls_back_gracefully() -> None:
    # If schwifty is not installed the rule should still pass (format is OK)
    with patch.dict("sys.modules", {"schwifty": None}):
        passed, message = _iban_format_valid(_TRADE, _CP, _ssi("GB29NWBK60161331926819"))
    assert passed is True
