"""Export the FastAPI OpenAPI contract to docs/api/openapi.json.

This snapshot is the canonical, reviewable API-contract artifact for the SDD
phase (see docs/ai-driven-development.md). Regenerate it whenever an endpoint,
request/response schema, or status code changes:

    uv run python scripts/export_openapi.py

CI runs tests/unit/test_openapi_contract.py, which fails if the committed
snapshot drifts from the live application — forcing the contract diff to appear
in the PR alongside the implementation change.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.main import app

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "api" / "openapi.json"


def render() -> str:
    """Return the OpenAPI document as deterministic JSON text."""
    spec = app.openapi()
    return json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
