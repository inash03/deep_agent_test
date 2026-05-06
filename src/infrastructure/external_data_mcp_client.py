"""Client facade for the external-data MCP server (SSE transport)."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from src.infrastructure.external_data_service import fetch_fx_rate as _direct_fetch


async def _fetch_via_mcp_async(base_currency: str, quote_currency: str) -> dict[str, Any]:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    mcp_url = os.environ.get("MCP_EXTERNAL_DATA_URL", "http://localhost:8080/sse")
    async with MultiServerMCPClient(
        {"external_data": {"url": mcp_url, "transport": "sse"}}
    ) as client:
        tools = await client.get_tools()
        tool = next(t for t in tools if t.name == "get_market_fx_rate")
        result = await tool.ainvoke(
            {"base_currency": base_currency, "quote_currency": quote_currency}
        )
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        for block in result:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    return parsed
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return {"error": "Unexpected MCP response format", "raw": str(result)}


def fetch_fx_rate_via_mcp(base_currency: str, quote_currency: str) -> dict[str, Any]:
    """Call the external-data MCP server, with a direct fallback for dev/test."""
    if os.getenv("MCP_EXTERNAL_DATA_DISABLE", "").lower() in {"1", "true", "yes"}:
        return _direct_fetch(base_currency, quote_currency)

    try:
        return asyncio.run(_fetch_via_mcp_async(base_currency, quote_currency))
    except Exception as exc:  # noqa: BLE001
        direct = _direct_fetch(base_currency, quote_currency)
        direct["mcp_fallback_reason"] = f"{type(exc).__name__}: {exc}"
        return direct
