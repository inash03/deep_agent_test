"""ECB FX rate helpers used by the MCP external-data server.

Framework-free so they can be unit-tested without starting an MCP server
or making live network calls.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

_ECB_URL = (
    "https://data-api.ecb.europa.eu/service/data/EXR/"
    "D.{ccy}.EUR.SP00.A?lastNObservations=1&format=jsondata"
)


def _fetch_eur_rate(ccy: str, timeout: float = 5.0) -> float | None:
    """Return how many units of *ccy* equal 1 EUR, or None on failure."""
    if ccy.upper() == "EUR":
        return 1.0
    try:
        resp = httpx.get(_ECB_URL.format(ccy=ccy.upper()), timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        obs = data["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]
        latest_key = max(obs.keys(), key=int)
        return float(obs[latest_key][0])
    except Exception:
        return None


def fetch_fx_rate(base_currency: str, quote_currency: str) -> dict[str, Any]:
    """Fetch the ECB reference cross-rate for *base_currency* / *quote_currency*.

    Returns a dict with ``rate``, ``base``, ``quote``, ``source``, ``note``
    on success, or ``error``, ``base``, ``quote`` on failure.
    """
    base = base_currency.upper()
    quote = quote_currency.upper()

    base_rate = _fetch_eur_rate(base)
    quote_rate = _fetch_eur_rate(quote)

    if base_rate is None or quote_rate is None:
        failed = base if base_rate is None else quote
        return {
            "error": f"ECB API unavailable or currency '{failed}' not supported",
            "base": base,
            "quote": quote,
        }

    # rate = how many quote units per 1 base unit
    rate = quote_rate / base_rate
    return {
        "rate": round(rate, 6),
        "base": base,
        "quote": quote,
        "source": "ECB Statistical Data Warehouse",
        "note": "Reference rate — indicative, not a dealing rate",
    }
