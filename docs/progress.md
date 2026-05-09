# Progress Log

## Current Status

**Branch:** `main`

**Last updated:** 2026-05-09

**Current focus:** Documentation refresh after the Next.js migration.

**Next:** Continue with the backlog in `docs/tasks.md`.

## Recent Log

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
