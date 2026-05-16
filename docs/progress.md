# Progress Log

## Current Status

**Branch:** `claude/enhance-auth-security-YtqHg`

**Last updated:** 2026-05-15

**Current focus:** Auth security hardening — brute-force / dictionary attack
protection and documentation update.

**Next:** Merge branch, then continue with the backlog in `docs/tasks.md`.

## Recent Log

### 2026-05-15 - Auth security hardening

Branch: `claude/enhance-auth-security-YtqHg`

Changes:

- `frontend/src/middleware.ts` (new): IP-based rate limiter on
  `POST /api/auth/callback/credentials` using `@upstash/ratelimit` +
  Upstash Redis (5 req / 10 min / IP; fail-open when Redis is absent).
- `frontend/src/account-lockout.ts` (new): per-username failure counter
  backed by Upstash Redis; locks account 15 min after 5 consecutive
  failures, resets on success.
- `frontend/src/auth.ts`: integrate account lockout checks; fix
  timing-based username enumeration by always running `bcrypt.compare`.
- `docs/requirements.md`: added FR-19, FR-20, three security NFRs, and
  expanded Authentication Requirements with a three-layer defence description.
- `docs/architecture.md`: updated Frontend Architecture table,
  Authentication and BFF section (ASCII flow diagram), and Environment
  Variables to document the new Upstash variables.
- `docs/tasks.md`: added backlog item for Next.js GHSA-26hh-7cqf-hhc6
  middleware-bypass CVE upgrade.

### 2026-05-09 - Documentation refresh

Files:

- `README.md`
- `docs/architecture.md`
- `docs/requirements.md`
- `docs/tasks.md`
- `docs/tasks_done.md`
- `docs/progress.md`
- `docs/demo_hybrid_agent.md`
- `frontend/.env.example`
- `CLAUDE.md`
- `.codex.md`
- `.openai/config.md`

Summary:

- Rewrote the README in Japanese.
- Rewrote project docs in English.
- Removed stale legacy frontend deployment wording.
- Documented the current Next.js App Router, Auth.js, BFF, Vercel, FastAPI,
  Cloud Run, and MCP architecture.
- Added Codex-facing project guidance derived from `CLAUDE.md`.

### 2026-05-09 - Next.js migration branch conflict resolution

Summary:

- Resolved conflicts in the frontend package files, version file, Playwright
  smoke tests, and backend deployment workflow.
- Kept Vercel as the frontend deployment path.
- Kept GitHub Actions focused on Cloud Run backend and MCP server deployment.

### 2026-05-06 - MCP server Cloud Run port hotfix

Summary:

- Updated the MCP external-data server to bind to `0.0.0.0` and use the Cloud
  Run `PORT` environment variable.

### 2026-05-05 - External-data MCP server

Summary:

- Added `mcp_server/` as a Cloud Run service for external market data.
- Added a client/fallback layer in the backend.
- Routed `get_market_fx_rate` through the MCP integration.

## Historical Notes

Older history was previously recorded in this file with mojibake. The important
completed milestones are summarized in `docs/tasks_done.md`.
