# Documentation Index

This directory is the system of record for the project. `CLAUDE.md` at the repo
root is a short map; the detail lives here. Read the document you need for the
task instead of loading everything.

## Working in the repo

- `development.md` — development process, task tracking, end-of-step checklist,
  git conventions, and useful commands.
- `testing.md` — TDD workflow, harness strategy, requirement coverage matrix,
  and known test gaps.
- `ai-driven-development.md` — the DDD/BDD/SDD/TDD phase pipeline, artifacts,
  ownership, and staged rollout.

## Architecture and conventions

- `architecture.md` — canonical system architecture (frontend, BFF, backend,
  data, hosting, CI/CD).
- `frontend.md` — Next.js App Router rules, UI language, and versioning.
- `backend.md` — FastAPI/LangGraph layering and API compatibility.
- `security.md` — secrets, key roles, and trust boundaries.

## Specifications and contracts

- `requirements.md` — project requirements (FR-01..).
- `api/openapi.json` — committed API contract; `api/README.md` explains it.
- `specs/` — data-model specs and the requirement coverage matrix.
- `domain/` — glossary, domain model, and context map (shared vocabulary).
- `adr/` — Architecture Decision Records.

## Status and planning

- Task state lives in **GitHub Issues / Projects** (the source of truth);
  see ADR-0002 and ADR-0008.
- `tasks.md` — ephemeral per-session agent scratchpad (working memory), not
  shared task state.
- `issue-drafts.md` — temporary staging for backlog being migrated to Issues;
  delete once the Issues are filed.
</content>
