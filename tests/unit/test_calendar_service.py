from src.infrastructure.calendar_service import (
    check_fx_value_date,
    currency_to_country,
    parse_fx_pair,
)


def test_parse_fx_pair_accepts_slash_and_compact_forms() -> None:
    assert parse_fx_pair("USD/JPY") == ("USD", "JPY")
    assert parse_fx_pair("USDJPY") == ("USD", "JPY")
    assert parse_fx_pair("eur-usd") == ("EUR", "USD")


def test_currency_to_country_uses_eur_default_and_override(monkeypatch) -> None:
    assert currency_to_country("EUR") == "DE"
    monkeypatch.setenv("MCP_EUR_COUNTRY", "FR")
    assert currency_to_country("EUR") == "FR"


def test_check_fx_value_date_detects_currency_holiday() -> None:
    def fetcher(year: int, country_code: str) -> list[dict]:
        if country_code == "JP":
            return [
                {
                    "date": "2026-05-05",
                    "name": "Children's Day",
                    "localName": "Children's Day",
                    "types": ["Public"],
                }
            ]
        return []

    result = check_fx_value_date("USD/JPY", "2026-05-05", fetcher=fetcher)

    assert result["status"] == "ok"
    assert result["is_business_day"] is False
    assert "JPY holiday: Children's Day" in result["reason"]


def test_check_fx_value_date_returns_unknown_on_fetch_failure() -> None:
    def fetcher(year: int, country_code: str) -> list[dict]:
        raise TimeoutError("slow calendar")

    result = check_fx_value_date("USD/JPY", "2026-05-05", fetcher=fetcher)

    assert result["status"] == "unknown"
    assert result["is_business_day"] is None
    assert "Holiday lookup failed" in result["reason"]
