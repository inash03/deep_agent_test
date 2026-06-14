# OpenAI/Codex Configuration Notes

This file gives OpenAI/Codex and other AI coding agents the same guidance as
`CLAUDE.md`: it is a **map, not a manual**. The system of record lives under
`docs/` (`docs/README.md` is the full index). Use common Markdown only so the
guidance is readable by any agent. Read the document you need for the task.

## Session Start

1. Check `git status --short --branch`.
2. Read the current task in `docs/tasks.md` and status in `docs/progress.md`.
3. Open the relevant documents from the map below; inspect only the files the
   task needs.

## Documentation Map

| Topic | Source of truth |
| --- | --- |
| How we work, commands, git, checklist | `docs/development.md` |
| Testing: TDD loop, harness, coverage matrix, gaps | `docs/testing.md` |
| AI-driven phase pipeline (DDD/BDD/SDD/TDD) | `docs/ai-driven-development.md` |
| System architecture | `docs/architecture.md` |
| Frontend rules, UI language, versioning | `docs/frontend.md` |
| Backend layering and API compatibility | `docs/backend.md` |
| Secrets, keys, trust boundaries | `docs/security.md` |
| Requirements | `docs/requirements.md` |
| API contract, specs, domain, ADRs | `docs/api/`, `docs/specs/`, `docs/domain/`, `docs/adr/` |

## Golden Rules

- Keep changes scoped to the task; do not refactor unrelated code or remove user
  changes; prefer existing patterns over new abstractions.
- Use test-driven development for every behavior change: write the smallest
  failing test first, then the smallest production change (`docs/testing.md`).
- Isolate external dependencies (Neon, Anthropic, OpenAI, ECB, MCP) in the
  default suite; real-service tests are opt-in integration tests
  (`docs/testing.md`).
- Browser API calls go through the BFF at `/api/backend/*`; never expose backend
  secrets via `NEXT_PUBLIC_*`; never commit `.env` or real secrets
  (`docs/security.md`).
- Preserve API backward compatibility; keep HITL write actions explicit
  (`docs/backend.md`).
- Update docs when architecture, env vars, endpoints, or deployment change.
- Do not report a task complete until relevant checks pass 100%, or a blocker is
  documented with the exact failing command and reason. Final responses must
  list the exact verification commands run and whether each passed.

## Quick Commands

Full command list is in `docs/development.md`. Completion gate:

```bash
pytest
cd frontend
npm run lint
npm run build
```

## Documentation Language

- `README.md` is Japanese.
- Files under `docs/`, and the agent instruction files `CLAUDE.md`, `.codex.md`,
  and `.openai/config.md`, are English.
</content>
