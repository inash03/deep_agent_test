"""MCP server exposing FX business-calendar tools.

Run locally with:
    python -m src.infrastructure.mcp.calendar_server
"""

from __future__ import annotations

from src.infrastructure.calendar_service import check_fx_value_date as _check_fx_value_date


def _build_server():
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("stp-calendar", json_response=True)

    @server.tool()
    def check_fx_value_date(instrument_id: str, value_date: str) -> dict:
        """Check whether an FX value date is a business day for both currencies."""
        return _check_fx_value_date(instrument_id, value_date)

    return server


def main() -> None:
    server = _build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
