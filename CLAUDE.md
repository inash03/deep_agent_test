# CLAUDE.md - Repository Map

This file is a **map, not a manual**. It points to the documents that are the
system of record under `docs/`. Read the document you need for the task instead
of loading everything. Keep this file short (~100 lines); put detail in `docs/`.

These instructions OVERRIDE default agent behavior. The linked documents carry
the same authority as this file.

## Session Start

1. Check `git status --short --branch`.
2. Read the current task in `docs/tasks.md` and status in `docs/progress.md`.
3. Open the documents relevant to the task from the map below.
4. Inspect only the files needed for the task.

## Documentation Map

`docs/README.md` is the full index. The documents you will need most:

| Topic | Source of truth |
| --- | --- |
| How we work, commands, git, checklist | `docs/development.md` |
| Testing: TDD loop, harness, coverage | `docs/testing.md` |
| AI-driven phase pipeline (DDD/BDD/SDD/TDD) | `docs/ai-driven-development.md` |
| System architecture | `docs/architecture.md` |
| Frontend rules, UI language, versioning | `docs/frontend.md` |
| Backend layering and API compatibility | `docs/backend.md` |
| Secrets, keys, trust boundaries | `docs/security.md` |
| Requirements | `docs/requirements.md` |
| API contract | `docs/api/openapi.json` |
| Specs, coverage matrix, data models | `docs/specs/` |
| Domain glossary, model, context map | `docs/domain/` |
| Architecture Decision Records | `docs/adr/` |

## Golden Rules

Non-negotiable guardrails. Follow the linked docs for the full detail.

- Keep changes scoped to the task. Do not refactor unrelated code or remove user
  changes. (`docs/development.md`)
- Use test-driven development for every behavior change: write the smallest
  failing test first. (`docs/testing.md`)
- Isolate external dependencies (DB, LLM, MCP) in the default test suite; never
  hit real Neon/Anthropic/OpenAI/Cloud Run from unit tests. (`docs/testing.md`)
- Browser code calls `/api/backend/*`; never expose backend secrets via
  `NEXT_PUBLIC_*`; never commit `.env` or real secrets. (`docs/security.md`)
- Keep HITL write actions explicit; do not let agents run arbitrary shell.
  (`docs/backend.md`, `docs/security.md`)
- Preserve backward compatibility for API changes. (`docs/backend.md`)
- Update docs when architecture, env vars, endpoints, or deployment change.
- Do not report a task complete until relevant checks pass 100%, or a blocker is
  documented with the exact failing command and reason.

## Architecture at a Glance

Next.js App Router frontend + BFF (`/api/backend/[...path]`) on Vercel; Python
3.12 FastAPI + LangGraph backend and an external-data MCP server on Cloud Run;
Neon PostgreSQL; Alembic migrations. The browser never calls Cloud Run directly.
Full detail and diagrams: `docs/architecture.md`.

## AI-Driven Development Process

This repo follows a DDD -> BDD -> SDD -> TDD pipeline where each phase produces a
reviewed artifact. The full process, artifacts, ownership, and rollout status
live in `docs/ai-driven-development.md` (§9 for current rollout state). Phase
skills under `.claude/skills/` drive each phase: `/ddd-update`, `/bdd-feature`,
`/sdd-spec`, `/tdd-implement`. Project subagents live in `.claude/agents/`
(`spec-reviewer`, `researcher`). Significant decisions are recorded as ADRs in
`docs/adr/`; model routing and managed-settings policy are in ADR-0004.

## Documentation Language

- `README.md` is Japanese.
- Files under `docs/`, plus `CLAUDE.md`, `.codex.md`, and `.openai/config.md`,
  are English.

## Quick Commands

Full command list is in `docs/development.md`. Completion gate:

```bash
pytest
cd frontend
npm run lint
npm run build
```
</content>
