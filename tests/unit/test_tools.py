"""Unit tests for LangGraph tools.

All tests are pure — no LLM calls, no network.
Tools return JSON strings; we parse and assert on the contents.
"""

import json

import pytest

from src.infrastructure import mock_store
from src.infrastructure.tools import (
    get_counterparty,
    get_reference_data,
    get_settlement_instructions,
    get_trade_detail,
    lookup_external_ssi,
    register_ssi,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def invoke(tool, **kwargs):
    """Call a @tool-decorated function and parse its JSON response."""
    return json.loads(tool.invoke(kwargs))


@pytest.fixture(autouse=True)
def restore_ssi_store():
    """Snapshot and restore _SSIS around each test that might write to it."""
    snapshot = dict(mock_store._SSIS)
    yield
    mock_store._SSIS.clear()
    mock_store._SSIS.update(snapshot)


# ---------------------------------------------------------------------------
# get_trade_detail
# ---------------------------------------------------------------------------


class TestGetTradeDetail:
    def test_existing_trade(self):
        result = invoke(get_trade_detail, trade_id="TRD-001")
        assert result["trade_id"] == "TRD-001"
        assert result["counterparty_lei"] == "213800QILIUD4ROSUO03"
        assert result["currency"] == "USD"
        assert result["instrument_id"] == "USDJPY"

    def test_unknown_trade_returns_error(self):
        result = invoke(get_trade_detail, trade_id="DOES-NOT-EXIST")
        assert "error" in result

    def test_all_five_scenarios_exist(self):
        for trade_id in ["TRD-001", "TRD-002", "TRD-003", "TRD-004", "TRD-005"]:
            result = invoke(get_trade_detail, trade_id=trade_id)
            assert result["trade_id"] == trade_id


# ---------------------------------------------------------------------------
# get_settlement_instructions
# ---------------------------------------------------------------------------


class TestGetSettlementInstructions:
    def test_ssi_found(self):
        # TRD-002 scenario: SSI exists for 5493001KJTIIGC8Y1R12 / EUR
        result = invoke(
            get_settlement_instructions,
            lei="5493001KJTIIGC8Y1R12",
            currency="EUR",
        )
        assert result["found"] is True
        assert result["bic"] == "GLSBUSS33"  # intentionally invalid BIC (test data)

    def test_ssi_not_found(self):
        # TRD-001 scenario: no internal SSI for 213800QILIUD4ROSUO03 / USD
        result = invoke(
            get_settlement_instructions,
            lei="213800QILIUD4ROSUO03",
            currency="USD",
        )
        assert result["found"] is False
        assert "message" in result

    def test_unknown_lei_not_found(self):
        result = invoke(
            get_settlement_instructions,
            lei="UNKNOWNLEI000000001",
            currency="USD",
        )
        assert result["found"] is False


# ---------------------------------------------------------------------------
# get_reference_data
# ---------------------------------------------------------------------------


class TestGetReferenceData:
    def test_known_instrument(self):
        result = invoke(get_reference_data, instrument_id="USDJPY")
        assert result["found"] is True
        assert result["asset_class"] == "FX"
        assert result["is_active"] is True

    def test_unknown_instrument(self):
        # TRD-005 scenario
        result = invoke(get_reference_data, instrument_id="UNKNOWN_CCY_PAIR")
        assert result["found"] is False


# ---------------------------------------------------------------------------
# get_counterparty
# ---------------------------------------------------------------------------


class TestGetCounterparty:
    def test_known_lei(self):
        result = invoke(get_counterparty, lei="213800QILIUD4ROSUO03")
        assert result["found"] is True
        assert result["name"] == "Acme Bank Ltd"

    def test_unknown_lei(self):
        # TRD-003 scenario
        result = invoke(get_counterparty, lei="UNKNOWNLEI000000001")
        assert result["found"] is False


# ---------------------------------------------------------------------------
# lookup_external_ssi
# ---------------------------------------------------------------------------


class TestLookupExternalSSI:
    def test_external_ssi_found(self):
        # TRD-001 scenario: external source has SSI → will trigger HITL
        result = invoke(
            lookup_external_ssi,
            lei="213800QILIUD4ROSUO03",
            currency="USD",
        )
        assert result["found"] is True
        assert result["source"] == "external"
        assert result["bic"] == "ACMEGB2L"

    def test_external_ssi_not_found(self):
        result = invoke(
            lookup_external_ssi,
            lei="UNKNOWNLEI000000001",
            currency="USD",
        )
        assert result["found"] is False


# ---------------------------------------------------------------------------
# register_ssi (write tool)
# ---------------------------------------------------------------------------


class TestRegisterSSI:
    def test_registers_successfully(self):
        result = invoke(
            register_ssi,
            lei="213800QILIUD4ROSUO03",
            currency="USD",
            bic="ACMEGB2L",
            account="GB29NWBK60161331926819",
        )
        assert result["success"] is True

    def test_registered_ssi_is_queryable(self):
        invoke(
            register_ssi,
            lei="213800QILIUD4ROSUO03",
            currency="USD",
            bic="ACMEGB2L",
            account="GB29NWBK60161331926819",
        )
        # Confirm it now appears in the internal store
        lookup = invoke(
            get_settlement_instructions,
            lei="213800QILIUD4ROSUO03",
            currency="USD",
        )
        assert lookup["found"] is True
        assert lookup["bic"] == "ACMEGB2L"
