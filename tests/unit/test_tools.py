"""Unit tests for LangGraph tools.

All tests are pure — no LLM calls, no network.
Tools return JSON strings; we parse and assert on the contents.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure import mock_store
from src.infrastructure.tools import (
    check_fx_value_date_calendar,
    get_counterparty,
    get_market_fx_rate,
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
        assert result["fx_rate"] == "151.25000000"
        assert result["trade_type"] == "Forward"
        assert result["input_date"] == "2026-04-01"

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
# check_fx_value_date_calendar
# ---------------------------------------------------------------------------


def test_check_fx_value_date_calendar_returns_mcp_result(monkeypatch):
    monkeypatch.setattr(
        "src.infrastructure.tools.check_fx_value_date_via_mcp",
        lambda instrument_id, value_date: {
            "status": "ok",
            "is_business_day": False,
            "instrument_id": instrument_id,
            "value_date": value_date,
            "reason": "JPY holiday: Children's Day",
        },
    )

    result = invoke(
        check_fx_value_date_calendar,
        instrument_id="USD/JPY",
        value_date="2026-05-05",
    )

    assert result["status"] == "ok"
    assert result["is_business_day"] is False
    assert "JPY holiday" in result["reason"]


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


# ---------------------------------------------------------------------------
# get_market_fx_rate (ECB API — mocked to avoid network calls)
# ---------------------------------------------------------------------------


def _ecb_mock_response(ccy: str, rate: float) -> MagicMock:
    """Build a minimal ECB JSON response mock for the given currency and rate."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "dataSets": [{"series": {"0:0:0:0:0": {"observations": {"0": [rate]}}}}]
    }
    return mock_resp


class TestGetMarketFxRate:
    """Tests for the get_market_fx_rate @tool (MCP disabled via env var)."""

    @pytest.fixture(autouse=True)
    def disable_mcp(self, monkeypatch):
        # Route through the direct ECB path so httpx mocks work without MCP server
        monkeypatch.setenv("MCP_EXTERNAL_DATA_DISABLE", "1")

    def test_usd_eur_rate_returned(self):
        # USD/EUR: EUR/USD = 1.10 → USD/EUR = 1/1.10 ≈ 0.909
        with patch("httpx.get", return_value=_ecb_mock_response("USD", 1.10)):
            result = invoke(get_market_fx_rate, base_currency="USD", quote_currency="EUR")
        assert "rate" in result
        assert result["base"] == "USD"
        assert result["quote"] == "EUR"
        assert abs(result["rate"] - (1.0 / 1.10)) < 0.01

    def test_cross_rate_usd_jpy(self):
        # EUR/USD=1.10, EUR/JPY=165.0 → USD/JPY = 165.0/1.10 = 150.0
        call_count = [0]

        def side_effect(url, timeout):
            mock = MagicMock()
            mock.raise_for_status = MagicMock()
            if "USD" in url:
                rate = 1.10
            else:
                rate = 165.0
            call_count[0] += 1
            mock.json.return_value = {
                "dataSets": [{"series": {"0:0:0:0:0": {"observations": {"0": [rate]}}}}]
            }
            return mock

        with patch("httpx.get", side_effect=side_effect):
            result = invoke(get_market_fx_rate, base_currency="USD", quote_currency="JPY")

        assert "rate" in result
        assert abs(result["rate"] - 150.0) < 0.01
        assert call_count[0] == 2  # two ECB calls made

    def test_eur_base_skips_api_call(self):
        # EUR/JPY: base is EUR (rate=1.0 by definition), only JPY call needed
        with patch("httpx.get", return_value=_ecb_mock_response("JPY", 165.0)) as mock_get:
            result = invoke(get_market_fx_rate, base_currency="EUR", quote_currency="JPY")
        assert "rate" in result
        assert abs(result["rate"] - 165.0) < 0.01
        mock_get.assert_called_once()  # only the JPY call

    def test_api_error_returns_error_key(self):
        with patch("httpx.get", side_effect=Exception("connection timeout")):
            result = invoke(get_market_fx_rate, base_currency="USD", quote_currency="EUR")
        assert "error" in result
        assert result["base"] == "USD"
        assert result["quote"] == "EUR"
