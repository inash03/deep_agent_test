"""MCP server exposing external-data tools (ECB FX rate).

This service is deployed as a separate Cloud Run instance.
Run locally with:
    python mcp_server/external_data_server.py
"""

from __future__ import annotations

from src.infrastructure.external_data_service import fetch_fx_rate as _fetch_fx_rate


def _build_server():
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("stp-external-data", json_response=True)

    @server.tool()
    def get_market_fx_rate(base_currency: str, quote_currency: str) -> dict:
        """Fetch the current ECB reference FX rate for a currency pair."""
        return _fetch_fx_rate(base_currency, quote_currency)

    return server


def main() -> None:
    server = _build_server()
    server.run(transport="sse")


if __name__ == "__main__":
    main()
