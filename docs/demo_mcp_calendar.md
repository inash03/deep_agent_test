# MCP Calendar Demo

This demo shows MCP as a small external tool server that LangGraph/FoAgent can
use during FoCheck and triage.

## What It Adds

- MCP server: `src.infrastructure.mcp.calendar_server`
- MCP client facade: `src.infrastructure.calendar_mcp_client`
- LangGraph tool: `check_fx_value_date_calendar`
- FoCheck rule result: `value_date_business_calendar`

The MCP server checks whether an FX value date is open in both currencies'
representative markets. It uses the Nager.Date public holiday API:

```text
GET https://date.nager.at/api/v3/PublicHolidays/{year}/{countryCode}
```

Default currency-to-country mapping:

| Currency | Calendar country |
| --- | --- |
| USD | US |
| JPY | JP |
| EUR | DE |
| GBP | GB |
| AUD | AU |
| CHF | CH |
| CAD | CA |
| NZD | NZ |

Override the EUR calendar country with `MCP_EUR_COUNTRY`, for example:

```powershell
$env:MCP_EUR_COUNTRY = "FR"
```

## Install Dependencies

```powershell
uv pip install -e ".[dev]"
```

The project dependencies include:

- `mcp[cli]`
- `langchain-mcp-adapters`

If those packages are not installed, the app falls back to the same calendar
service directly so local development can still run. Set
`MCP_CALENDAR_DIRECT_FALLBACK=false` to require real MCP calls.

## Run The MCP Server Directly

```powershell
python -m src.infrastructure.mcp.calendar_server
```

This starts a stdio MCP server. It is normally launched automatically by the
LangChain MCP adapter, so direct execution is mainly useful to confirm imports.

## Try The Demo Trade

Seed data includes `TRD-014`, a `USD/JPY` trade with value date `2026-05-05`.
That date is a Japanese public holiday, so FoCheck should produce:

```text
rule_name = value_date_business_calendar
passed = false
severity = error
```

Run:

```powershell
python -m src.infrastructure.seed
uvicorn src.main:app --reload
```

Then call:

```powershell
curl -X POST http://localhost:8000/api/v1/trades/TRD-014/fo-check
```

Expected behavior:

- The response includes a failed `value_date_business_calendar` result.
- The trade moves to `FoAgentToCheck`.
- Starting FO triage lets FoAgent see and explain the MCP calendar failure.

## Useful Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `MCP_EUR_COUNTRY` | `DE` | Representative holiday calendar for EUR |
| `MCP_CALENDAR_HTTP_TIMEOUT_SECONDS` | `5` | Nager.Date request timeout |
| `MCP_CALENDAR_DISABLE` | unset | Set true to skip the calendar lookup |
| `MCP_CALENDAR_DIRECT_FALLBACK` | `true` | Use direct service if MCP packages/server fail |
