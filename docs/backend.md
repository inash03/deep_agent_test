# Backend Guide

Conventions for the Python 3.12 / FastAPI / LangGraph backend. See
`docs/architecture.md` for the overall system shape and `docs/testing.md` for
the harness strategy.

## Layering

- Keep presentation, domain, and infrastructure concerns separated.
- Validate external input with Pydantic schemas.
- Keep HITL write actions explicit.
- Do not let agents execute arbitrary shell commands.

## API Compatibility

- Preserve backward compatibility for API changes when frontend and backend can
  deploy independently.
- The API contract is committed at `docs/api/openapi.json` and verified by
  `tests/unit/test_openapi_contract.py`. Regenerate it with
  `uv run python scripts/export_openapi.py` when endpoints change.
</content>
