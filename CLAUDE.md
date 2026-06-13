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
- Use test-driven development for every behavior change. Write or update the
  smallest meaningful test before implementing production code.
- Do not report a task as complete until the relevant automated checks pass
  100%, or until a blocker is clearly documented with the exact failing command
  and failure reason.

## AI-Driven Development Process (DDD/BDD/SDD/TDD)

This repository is adopting a team-scale, AI-driven development process. The
full process, artifacts, ownership, and staged rollout are defined in
`docs/ai-driven-development.md`. Read it before starting feature work.

- Significant technical decisions are recorded as ADRs in `docs/adr/`.
- Domain vocabulary and model live in `docs/domain/` (glossary, model,
  context map). Use this vocabulary in code, tests, and UI.
- Behavior is specified as executable Gherkin in `features/`, with step
  definitions in `tests/bdd/`. Every `.feature` file is run by CI.
- Phase skills under `.claude/skills/` drive each phase: `/ddd-update`,
  `/bdd-feature`, `/sdd-spec`, `/tdd-implement`.

Rollout status (see `docs/ai-driven-development.md` §9): **Phase 1 done,
Phase 2 in progress**. SDD is active: the API contract is committed at
`docs/api/openapi.json` and verified by `tests/unit/test_openapi_contract.py`
(regenerate with `uv run python scripts/export_openapi.py`). Detailed scenarios
live in `features/specs/*.spec.feature`; data-model specs in `docs/specs/`.

## Mandatory TDD Workflow

See `docs/testing.md` for the full test strategy, harness rules, requirement
coverage matrix, and known test gaps.

Agents must run the red-green-refactor loop autonomously:

1. Identify the behavior surface and the closest existing test file.
2. Write a failing test first:
   - Backend domain logic: add or update `tests/unit/test_*.py`.
   - Backend API behavior: add or update a focused pytest using FastAPI/httpx
     test clients or repository/service harnesses.
   - Frontend type or UI behavior: add a focused TypeScript/React test when a
     local test harness exists; otherwise add or update Playwright coverage in
     `frontend/tests/e2e/*.spec.ts` for user-visible flows.
   - Documentation-only changes may skip new tests, but still run the relevant
     verification commands listed below.
3. Run the focused test and confirm it fails for the expected reason.
4. Implement the smallest production change that can make the test pass.
5. Run the focused test again until it passes.
6. Run the full relevant suite before final reporting.
7. Refactor only after tests are green, and rerun the affected tests after each
   refactor.

Never replace this loop with manual inspection when an automated harness can be
written or extended.

## Harness Engineering Strategy

External dependencies must be isolated by default so tests are deterministic,
fast, and safe to run without manual environment setup.

- Database:
  - Prefer repository or service-level tests with in-memory fakes, transaction
    rollbacks, or explicit test fixtures instead of touching Neon PostgreSQL.
  - Tests that require a real database must be clearly marked as integration
    and must not run in the default `pytest` suite.
- LLM providers:
  - Never call Anthropic or OpenAI from unit tests.
  - Stub model clients, LangGraph nodes, cost trackers, and embeddings at the
    boundary where they enter infrastructure code.
  - Assert prompts, routing decisions, tool choices, state transitions, and
    persisted outputs rather than provider responses.
- External APIs and MCP:
  - Use local fakes or monkeypatched clients for ECB/external-data/MCP calls.
  - Keep the fallback behavior testable without network access.
- HTTP/BFF:
  - Browser code must call `/api/backend/*`; tests should assert this contract
    instead of calling Cloud Run directly.
  - FastAPI protected endpoints should be tested with explicit `X-API-Key`
    harness values when authentication behavior is part of the change.
- Time, randomness, and environment:
  - Freeze or inject clocks for date-sensitive rules.
  - Use deterministic IDs and seed data in tests.
  - Patch environment variables in the test harness rather than relying on a
    developer's shell.
- E2E:
  - Keep Playwright smoke tests focused on critical operator flows.
  - Use local dev servers and test credentials; do not depend on production
    Vercel, Cloud Run, Neon, or real LLM credentials.

## Task Tracking

Task state is represented by section position in `docs/tasks.md`.

| Section | Meaning |
| --- | --- |
| `## In Progress` | Currently active task |
| `## Backlog` | Planned but not started |

Completed tasks are summarized in `docs/tasks_done.md`.

## End-of-Step Checklist

1. Run relevant checks until they pass 100%.
2. Update docs if behavior, architecture, env vars, or deployment changed.
3. Update `docs/progress.md` with a concise entry.
4. Move completed task notes to `docs/tasks_done.md` when appropriate.
5. Summarize changes and verification for the user, including exact commands
   run and whether each passed.

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
# Install/update backend dev dependencies when needed
uv pip install -e ".[dev]"

# Default backend test suite; excludes tests marked integration
pytest

# Equivalent uv invocation
uv run pytest

# Focused TDD loop examples
uv run pytest tests/unit/test_check_rules.py -v
uv run pytest tests/unit/test_gather_context_routing.py -v

# Integration tests that may require real services or credentials
uv run pytest tests/integration -m integration -v

# Static checks
ruff check .
mypy src

# Local backend server
alembic upgrade head
uvicorn src.main:app --reload
```

Frontend:

```bash
cd frontend

# Install frontend dependencies when needed
npm install

# TypeScript check; this repository uses it as the lint command
npm run lint

# Production build
npm run build

# Local dev server
npm run dev

# Playwright E2E tests; requires a running frontend unless configured otherwise
npm run test:e2e
```

Recommended completion gate:

```bash
pytest
cd frontend
npm run lint
npm run build
```
