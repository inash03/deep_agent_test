# API contract (OpenAPI)

`openapi.json` in this directory is the **canonical API-contract artifact** for
the SDD phase. It is the backend `/api/v1/*` contract that the Next.js BFF
(`/api/backend/*`) forwards to.

## How it is kept honest

The snapshot is generated from the FastAPI application and verified in CI:

- Regenerate after any endpoint / schema / status-code change:

  ```bash
  uv run python scripts/export_openapi.py
  ```

- `tests/unit/test_openapi_contract.py` fails if the committed snapshot drifts
  from the live application. This forces the contract diff to appear in the PR
  next to the implementation change, so reviewers see the contract impact.

## Transitional note

Today the contract is **derived from the implementation and locked by the drift
test** (see ADR-0003). The target state is spec-first for new endpoints: write
the contract, review it, then implement against it. The drift test is the
mechanism that makes either direction safe.
