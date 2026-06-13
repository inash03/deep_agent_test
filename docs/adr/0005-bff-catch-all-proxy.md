# ADR-0005: BFF catch-all proxy for browser-to-backend calls

- **Status:** Accepted (retrospective)
- **Date:** 2026-06-13
- **Deciders:** Architecture team (recorded retrospectively)
- **Supersedes:** none
- **Superseded by:** none

## Context

This ADR records a decision already embodied in the code, captured during the
brownfield retrofit (see `docs/specs/coverage-matrix.md`). The browser must not
hold the backend API key or call Cloud Run directly. A boundary is needed
between browser code and the FastAPI `/api/v1/*` contract.

## Decision

Browser requests go through a single Next.js catch-all Route Handler at
`frontend/src/app/api/backend/[...path]/route.ts`, which:

- Requires an Auth.js session (`auth()`); returns 401 otherwise.
- Forwards all methods (GET/POST/PATCH/PUT/DELETE) to `BACKEND_API_URL`.
- Strips hop-by-hop headers and `cookie`, and injects `X-API-Key` from
  `BACKEND_API_KEY` server-side so the key never reaches the browser.
- Uses `cache: 'no-store'` and streams the upstream response back.

We chose one generic proxy over individually typed BFF endpoints per route.

## Consequences

- The API key stays server-side (FR-14) and every business call is gated by an
  Auth.js session (FR-13) in one place.
- New backend endpoints need no BFF change — the catch-all forwards them.
- The proxy is untyped: it does not validate request/response shapes (the
  FastAPI contract and `docs/api/openapi.json` own that). A bug in the proxy
  affects all routes at once, so it deserves a focused integration test
  (tracked in the coverage matrix, Tier 4).

## Alternatives considered

- **Per-endpoint typed BFF handlers.** Rejected: more code and a change for
  every new endpoint, with little benefit given the backend already validates.
- **Browser calls Cloud Run directly.** Rejected: would expose the API key and
  duplicate auth at the edge.
