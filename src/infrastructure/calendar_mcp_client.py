"""Client facade for the FX calendar MCP server."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from src.infrastructure.calendar_service import check_fx_value_date as _direct_check


async def _check_via_mcp_async(instrument_id: str, value_date: str) -> dict[str, Any]:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient(
        {
            "calendar": {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["-m", "src.infrastructure.mcp.calendar_server"],
            }
        }
    )
    tools = await client.get_tools()
    tool = next(t for t in tools if t.name == "check_fx_value_date")
    result = await tool.ainvoke({"instrument_id": instrument_id, "value_date": value_date})
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
    return {"status": "unknown", "is_business_day": None, "reason": str(result)}


def check_fx_value_date_via_mcp(instrument_id: str, value_date: str) -> dict[str, Any]:
    """Call the local calendar MCP server, with a direct fallback for dev/test."""
    if os.getenv("MCP_CALENDAR_DISABLE", "").lower() in {"1", "true", "yes"}:
        return {
            "status": "unknown",
            "is_business_day": None,
            "instrument_id": instrument_id,
            "value_date": value_date,
            "reason": "MCP calendar lookup disabled by MCP_CALENDAR_DISABLE.",
            "markets": [],
        }

    try:
        return asyncio.run(_check_via_mcp_async(instrument_id, value_date))
    except Exception as exc:  # noqa: BLE001
        if os.getenv("MCP_CALENDAR_DIRECT_FALLBACK", "true").lower() in {"1", "true", "yes"}:
            direct = _direct_check(instrument_id, value_date)
            direct["mcp_fallback_reason"] = f"{type(exc).__name__}: {exc}"
            return direct
        return {
            "status": "unknown",
            "is_business_day": None,
            "instrument_id": instrument_id,
            "value_date": value_date,
            "reason": f"MCP calendar lookup failed: {type(exc).__name__}: {exc}",
            "markets": [],
        }
