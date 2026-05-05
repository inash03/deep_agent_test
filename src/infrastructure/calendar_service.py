"""FX business-calendar lookup helpers used by the MCP calendar server.

The functions in this module are intentionally framework-free so they can be
unit-tested without starting an MCP server or making live network calls.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import date
from functools import lru_cache
from typing import Any, Callable

_CCY_TO_COUNTRY = {
    "USD": "US",
    "JPY": "JP",
    "GBP": "GB",
    "AUD": "AU",
    "CHF": "CH",
    "CAD": "CA",
    "NZD": "NZ",
}

_NAGER_BASE_URL = "https://date.nager.at/api/v3"
_SUPPORTED_CCY_RE = re.compile(r"^[A-Z]{3}$")

HolidayFetcher = Callable[[int, str], list[dict[str, Any]]]


def parse_fx_pair(instrument_id: str) -> tuple[str, str]:
    """Parse common FX instrument IDs such as USD/JPY, USDJPY, or EUR-USD."""
    normalized = re.sub(r"[^A-Z]", "", instrument_id.upper())
    if len(normalized) != 6:
        raise ValueError(f"Unsupported FX instrument format: {instrument_id!r}")
    base, quote = normalized[:3], normalized[3:]
    if not (_SUPPORTED_CCY_RE.match(base) and _SUPPORTED_CCY_RE.match(quote)):
        raise ValueError(f"Unsupported FX instrument format: {instrument_id!r}")
    return base, quote


def currency_to_country(currency: str) -> str:
    """Map a currency to a representative public-holiday country code."""
    ccy = currency.upper()
    if ccy == "EUR":
        return os.getenv("MCP_EUR_COUNTRY", "DE").upper()
    try:
        return _CCY_TO_COUNTRY[ccy]
    except KeyError as exc:
        raise ValueError(f"No holiday-country mapping configured for currency {ccy!r}") from exc


@lru_cache(maxsize=128)
def _fetch_public_holidays(year: int, country_code: str) -> list[dict[str, Any]]:
    url = f"{_NAGER_BASE_URL}/PublicHolidays/{year}/{country_code.upper()}"
    timeout = float(os.getenv("MCP_CALENDAR_HTTP_TIMEOUT_SECONDS", "5"))
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError(f"Unexpected holiday API response for {country_code}: {data!r}")
    return data


def check_fx_value_date(
    instrument_id: str,
    value_date: str,
    fetcher: HolidayFetcher | None = None,
) -> dict[str, Any]:
    """Check whether an FX value date is open in both currencies' markets."""
    try:
        parsed_date = date.fromisoformat(value_date)
        currencies = parse_fx_pair(instrument_id)
        countries = [currency_to_country(ccy) for ccy in currencies]
    except ValueError as exc:
        return {
            "status": "unknown",
            "is_business_day": None,
            "instrument_id": instrument_id,
            "value_date": value_date,
            "reason": str(exc),
            "markets": [],
        }

    markets: list[dict[str, Any]] = []
    fetch = fetcher or _fetch_public_holidays
    try:
        for currency, country in zip(currencies, countries):
            holidays = fetch(parsed_date.year, country)
            matching = [h for h in holidays if h.get("date") == value_date]
            markets.append(
                {
                    "currency": currency,
                    "country_code": country,
                    "is_weekend": parsed_date.weekday() >= 5,
                    "holidays": [
                        {
                            "date": h.get("date"),
                            "name": h.get("name"),
                            "local_name": h.get("localName"),
                            "types": h.get("types", []),
                        }
                        for h in matching
                    ],
                }
            )
    except (OSError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {
            "status": "unknown",
            "is_business_day": None,
            "instrument_id": instrument_id,
            "value_date": value_date,
            "currencies": list(currencies),
            "countries": countries,
            "reason": f"Holiday lookup failed: {type(exc).__name__}: {exc}",
            "markets": markets,
        }

    closed_markets = [
        m for m in markets
        if m["is_weekend"] or m["holidays"]
    ]
    if closed_markets:
        names = []
        for market in closed_markets:
            if market["is_weekend"]:
                names.append(f"{market['currency']} market weekend")
            for holiday in market["holidays"]:
                names.append(f"{market['currency']} holiday: {holiday.get('name')}")
        reason = "; ".join(names)
    else:
        reason = "Value date is open in both currency markets."

    return {
        "status": "ok",
        "is_business_day": not closed_markets,
        "instrument_id": instrument_id,
        "value_date": value_date,
        "currencies": list(currencies),
        "countries": countries,
        "reason": reason,
        "markets": markets,
        "source": "Nager.Date",
    }
