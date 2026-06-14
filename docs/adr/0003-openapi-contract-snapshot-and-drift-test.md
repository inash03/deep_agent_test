# ADR-0003: OpenAPI contract snapshot with drift test

- **Status:** Accepted
- **Date:** 2026-06-13
- **Deciders:** Architecture team
- **Supersedes:** none
- **Superseded by:** none

## Context

Phase 2 of the AI-driven development process (ADR-0002) adopts SDD, where the
API contract is a first-class, reviewed artifact. The backend is an existing
FastAPI application that generates its OpenAPI document at runtime, so a pure
"spec-first" approach would require restructuring every endpoint at once. We
need a contract artifact that (a) is reviewable in PRs, (b) is verified by CI
without new infrastructure, and (c) does not require a real database, LLM, or
network to check.

## Decision

We will commit the generated OpenAPI document to `docs/api/openapi.json` and
verify it with a drift test in the default pytest suite:

- `scripts/export_openapi.py` renders the contract deterministically
  (sorted keys, stable formatting) from `src.main:app`.
- `tests/unit/test_openapi_contract.py` regenerates the contract in-memory and
  fails if it differs from the committed snapshot, or if any path leaves the
  `/api/v1/*` contract.

For now the contract is **derived from the implementation and locked by the
drift test** (implementation-as-source, contract-as-checked). For new endpoints
the target is spec-first: write and review the contract, then implement against
it. The same drift test makes both directions safe.

## Consequences

- Any endpoint or schema change must regenerate the snapshot, so the contract
  diff appears in the PR for review (CODEOWNERS routes `docs/api/` to the
  architect).
- No new CI infrastructure: the check runs inside the existing `uv run pytest`
  job. Node-based linting (e.g. Spectral) and spec fuzzing (e.g. schemathesis)
  remain optional future additions, tracked in `docs/tasks.md`.
- The drift test is implementation-coupled by design; it detects unreviewed
  contract changes rather than enforcing a hand-written spec.

## Alternatives considered

- **Spectral lint + hand-written OpenAPI as the sole source.** Rejected for now:
  requires a Node toolchain in the Python CI job and a large up-front rewrite of
  the existing auto-generated contract.
- **schemathesis property-based contract tests.** Deferred: needs a running app
  and database, so it belongs in the integration suite, not the default gate.
- **No committed contract (rely on runtime OpenAPI only).** Rejected: nothing to
  review in a PR and no drift signal.
