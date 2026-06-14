"""Contract drift test for the committed OpenAPI snapshot.

The SDD phase treats docs/api/openapi.json as the canonical API contract
artifact. This test fails if the live FastAPI application no longer matches the
committed snapshot, forcing the contract change to be reviewed in the PR.

To update the snapshot intentionally:

    uv run python scripts/export_openapi.py
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.export_openapi import render

SNAPSHOT = Path(__file__).resolve().parent.parent.parent / "docs" / "api" / "openapi.json"


def test_committed_openapi_matches_application() -> None:
    assert SNAPSHOT.exists(), (
        "docs/api/openapi.json is missing. Run: uv run python scripts/export_openapi.py"
    )

    committed = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    live = json.loads(render())

    assert committed == live, (
        "OpenAPI contract drift detected: the application no longer matches "
        "docs/api/openapi.json. If this change is intended, regenerate the "
        "snapshot with: uv run python scripts/export_openapi.py"
    )


def test_openapi_snapshot_is_well_formed() -> None:
    spec = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    assert spec.get("openapi", "").startswith("3."), "expected an OpenAPI 3.x document"
    assert spec.get("paths"), "contract must declare at least one path"
    # The BFF contract is /api/v1/*; guard against accidental prefix changes.
    assert all(p.startswith("/api/v1/") for p in spec["paths"]), (
        "all backend paths must live under the /api/v1/* contract"
    )
