# CLAUDE.md - Repository Instructions

This file defines project-specific rules for Claude Code and other coding
agents working in this repository.

## Session Start

1. Check `git status --short --branch`.
2. Read the current task in `docs/tasks.md`.
3. Read the current status in `docs/progress.md`.
4. Inspect only the files needed for the task.

## Current Architecture

- Frontend: Next.js App Router, React, TypeScript, Auth.js.
- BFF: Next.js Route Handler at `/api/backend/[...path]`.
- Backend: Python 3.12, FastAPI, LangGraph, SQLAlchemy, Alembic.
- Database: Neon PostgreSQL.
- External data: MCP external-data server on Cloud Run.
- Hosting: Vercel for frontend, Cloud Run for backend and MCP services.
- CI/CD: Vercel Git Integration for frontend, GitHub Actions for Cloud Run.

The old static frontend deployment path is retired.

## Development Process

- Keep changes scoped to the requested task.
- Prefer existing patterns over new abstractions.
- Do not refactor unrelated code.
- Do not remove user changes.
- Update documentation when architecture, environment variables, endpoints, or
  deployment behavior changes.

## Task Tracking

Task state is represented by section position in `docs/tasks.md`.

| Section | Meaning |
| --- | --- |
| `## In Progress` | Currently active task |
| `## Backlog` | Planned but not started |

Completed tasks are summarized in `docs/tasks_done.md`.

## End-of-Step Checklist

1. Run relevant checks.
2. Update docs if behavior, architecture, env vars, or deployment changed.
3. Update `docs/progress.md` with a concise entry.
4. Move completed task notes to `docs/tasks_done.md` when appropriate.
5. Summarize changes and verification for the user.

## Git Conventions

Use concise conventional commit summaries when committing:

```text
docs: update Next.js architecture docs
fix: harden credentials auth configuration
feat: add trade search modal
```

Claude-authored commits may include:

```text
Generated-by: Claude (claude.ai/code)
```

## Frontend Rules

- Use Next.js App Router conventions.
- Keep `layout.tsx` and route `page.tsx` files server components unless client
  behavior is required.
- Put interactive migrated screens in `frontend/src/screens/` as client
  components.
- Browser-side API calls must go to `/api/backend/*`.
- Do not expose backend secrets through `NEXT_PUBLIC_*`.
- Protected business pages must require Auth.js login.
- `/login` is public.
- Global font configuration lives in `frontend/src/app/layout.tsx` and
  `frontend/src/app/globals.css`.

## Frontend UI Language

- Business UI text should be English.
- The Home screen may provide English/Japanese switching.
- The Home screen default language must be English.
- Avoid mojibake. If text appears corrupted, rewrite it from the intended
  meaning instead of preserving broken bytes.

## Frontend Versioning

- `frontend/package.json` contains the display version.
- `frontend/src/version.ts` may show the short Vercel commit SHA.
- Bump the frontend version for user-visible frontend changes.
- Do not bump the frontend version for backend-only or docs-only changes unless
  release policy explicitly requires it.

## Backend Rules

- Keep presentation, domain, and infrastructure concerns separated.
- Validate external input with Pydantic schemas.
- Keep HITL write actions explicit.
- Do not let agents execute arbitrary shell commands.
- Preserve backward compatibility for API changes when frontend and backend can
  deploy independently.

## Security Rules

- Never commit `.env` or real secret values.
- Store secrets in Vercel, GitHub Environments, Cloud Run secrets, or local
  `.env` files.
- `AUTH_SECRET` is for Auth.js session/JWT protection only.
- `BACKEND_API_KEY` is used by the Next.js BFF when calling FastAPI.
- FastAPI uses `API_KEY` to validate protected backend requests.

## Documentation Language

- `README.md` is Japanese.
- Files under `docs/` are English.
- `CLAUDE.md`, `.codex.md`, and `.openai/config.md` are English.

## Useful Commands

Backend:

```bash
pytest
alembic upgrade head
uvicorn src.main:app --reload
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
npm run dev
npm run test:e2e
```
