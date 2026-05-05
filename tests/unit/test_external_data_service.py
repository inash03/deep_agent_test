"""Unit tests for external_data_service (pure ECB logic, no MCP server needed)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.external_data_service import fetch_fx_rate, _fetch_eur_rate


def _ecb_response(rate: float) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {
        "dataSets": [{"series": {"0:0:0:0:0": {"observations": {"0": [rate]}}}}]
    }
    return mock


class TestFetchEurRate:
    def test_eur_returns_one_without_http(self):
        with patch("httpx.get") as mock_get:
            rate = _fetch_eur_rate("EUR")
        assert rate == 1.0
        mock_get.assert_not_called()

    def test_usd_fetches_and_returns_rate(self):
        with patch("httpx.get", return_value=_ecb_response(1.10)):
            rate = _fetch_eur_rate("USD")
        assert rate == pytest.approx(1.10)

    def test_api_failure_returns_none(self):
        with patch("httpx.get", side_effect=Exception("timeout")):
            rate = _fetch_eur_rate("USD")
        assert rate is None

    def test_lowercase_currency_normalized(self):
        with patch("httpx.get", return_value=_ecb_response(1.10)) as mock_get:
            _fetch_eur_rate("usd")
        called_url = mock_get.call_args[0][0]
        assert "USD" in called_url


class TestFetchFxRate:
    def test_usd_eur_rate(self):
        # EUR/USD=1.10 → USD/EUR ≈ 0.909
        with patch("httpx.get", return_value=_ecb_response(1.10)):
            result = fetch_fx_rate("USD", "EUR")
        assert "rate" in result
        assert result["base"] == "USD"
        assert result["quote"] == "EUR"
        assert result["rate"] == pytest.approx(1.0 / 1.10, rel=1e-4)

    def test_cross_rate_usd_jpy(self):
        # EUR/USD=1.10, EUR/JPY=165.0 → USD/JPY = 165.0/1.10 = 150.0
        def _side_effect(url, timeout):
            mock = MagicMock()
            mock.raise_for_status = MagicMock()
            rate = 1.10 if "USD" in url else 165.0
            mock.json.return_value = {
                "dataSets": [{"series": {"0:0:0:0:0": {"observations": {"0": [rate]}}}}]
            }
            return mock

        with patch("httpx.get", side_effect=_side_effect):
            result = fetch_fx_rate("USD", "JPY")

        assert "rate" in result
        assert result["rate"] == pytest.approx(150.0, rel=1e-4)

    def test_eur_base_skips_api_call(self):
        with patch("httpx.get", return_value=_ecb_response(165.0)) as mock_get:
            result = fetch_fx_rate("EUR", "JPY")
        assert "rate" in result
        assert result["rate"] == pytest.approx(165.0, rel=1e-4)
        mock_get.assert_called_once()

    def test_api_error_returns_error_key(self):
        with patch("httpx.get", side_effect=Exception("connection refused")):
            result = fetch_fx_rate("USD", "EUR")
        assert "error" in result
        assert result["base"] == "USD"
        assert result["quote"] == "EUR"

    def test_eur_eur_rate_is_one(self):
        with patch("httpx.get") as mock_get:
            result = fetch_fx_rate("EUR", "EUR")
        assert result["rate"] == pytest.approx(1.0)
        mock_get.assert_not_called()
