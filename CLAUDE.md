# CLAUDE.md — Development Rules

This file defines the rules Claude must follow when working in this repository.
Read this file before starting any task.

---

## Session Start Protocol

At the start of every session:
1. Read `docs/tasks.md` to find "In Progress" task
2. Read `docs/progress.md` (last 2 steps only) for context
3. Read only the files directly relevant to that task

---

## Development Process

- Work **step by step**; never implement everything at once
- **Clarify requirements** before writing code — ask if anything is unclear
- Do **NOT** refactor code unless explicitly instructed
- Do **NOT** add features, helpers, or abstractions beyond what was asked

### Task state transitions

Tasks move between sections in `docs/tasks.md`. Checkbox marks (`[x]`) are NOT used.
Position = state:

| Section | Meaning |
|---------|---------|
| `## Backlog` | Not yet started |
| `## In Progress` | Currently being worked on (max 1 task at a time) |

Completed tasks are archived to `docs/tasks_done.md` (not kept in tasks.md).

**Transition rules:**
- **Before writing code:** Move the task from Backlog → In Progress
- **After committing:** Move the task from In Progress to `docs/tasks_done.md` (one-line summary)

### End-of-step checklist (execute in order)

1. Commit the code change
2. Move completed task: cut from In Progress in `docs/tasks.md`, append one-line summary to `docs/tasks_done.md`
3. Move next task: Backlog → In Progress (in `docs/tasks.md`)
4. Update `docs/progress.md`: replace "Current Status" block at top and append to log
5. If the change affects architecture (new files, new endpoints, new DB tables, agent graph changes): update `docs/architecture.md`
6. If requirements changed or a new FR was fulfilled: update `docs/requirements.md`
7. Summarize what was done and propose next steps to the user

### Tracking files

- `docs/progress.md` — progress log (updated every step)
- `docs/tasks.md` — active task list (In Progress + Backlog only)
- `docs/tasks_done.md` — completed task archive (append-only)
- `docs/requirements.md` — feature requirements (update when FRs are added or completed)
- `docs/architecture.md` — system design (update when architecture changes)

---

## Git Conventions

### Commit Format — Conventional Commits

```
<type>: <short summary>

<optional body>

Generated-by: Claude (claude.ai/code)
```

**Types:** `feat` · `fix` · `chore` · `docs` · `refactor` *(only when instructed)* · `test`

**Rules:**
- Every commit containing code created or modified by Claude **MUST** include the footer:
  ```
  Generated-by: Claude (claude.ai/code)
  ```
- Keep the summary line under 72 characters
- Use imperative mood in the summary ("add feature" not "added feature")

### Branch Naming

```
feature/<short-description>
fix/<short-description>
chore/<short-description>
```

### Git Push

Always use:
```bash
git push -u origin <branch-name>
```

---

## Architecture

### Stack (current scope)

- **Backend:** Python + FastAPI + LangGraph
- **Frontend:** Out of scope for now (React, to be added later)

### Three-Layer Clean Architecture

Strict rule: **no cross-layer imports** (presentation must not import infrastructure directly, etc.)

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| Presentation | `src/presentation/` | FastAPI routers, request/response schemas |
| Domain | `src/domain/` | Entities, use cases, interfaces (pure business logic — no framework deps) |
| Infrastructure | `src/infrastructure/` | LangGraph agents, external APIs, DB access |

### Package Structure

```
deep_agent_test/
  src/
    presentation/   # FastAPI routers, Pydantic request/response schemas
    domain/         # entities, use cases, repository interfaces
    infrastructure/ # LangGraph agents, external API clients, DB
  tests/
    unit/
    integration/
  docs/
    progress.md
    requirements.md
    tasks.md
  CLAUDE.md
  pyproject.toml
  .env.example      # committed — keys only, no values
  .env              # NOT committed — actual secrets
```

---

## Naming Conventions

### Python

| Item | Convention | Example |
|------|-----------|---------|
| Variables | `snake_case` | `user_input` |
| Functions | `snake_case` | `run_agent()` |
| Modules / files | `snake_case` | `agent_runner.py` |
| Classes | `PascalCase` | `AgentRunner` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Private members | `_leading_underscore` | `_internal_state` |

---

## Security Rules

1. **API keys and secrets** must be stored in `.env` — never hardcoded in source files
2. **`.env` must never be committed** — verify it is listed in `.gitignore`
3. **`.env.example`** must always be committed (keys only, values empty or descriptive placeholders)
4. **All user input and external data** must be validated via Pydantic models before use
5. **Dependencies must be pinned** in `pyproject.toml` (exact versions at setup time)
6. **LangGraph agents:**
   - Minimize tool permissions — grant only what is necessary
   - Validate tool outputs before using them in downstream logic
   - Never allow agents to execute arbitrary shell commands without explicit user authorization

---

## Dependency Management

- Use `pyproject.toml` with pinned versions
- Prefer `uv` for package management; fall back to `pip` + `requirements.txt` if needed
- Do not upgrade dependencies without explicit instruction

---

## Frontend Versioning

The frontend has a single source of truth for its version: `frontend/src/version.ts`.

```ts
export const VERSION = '0.1.0'
```

### Semantic Versioning Policy (semver)

Follow **major.minor.patch** rules:

| Increment | When |
|-----------|------|
| `patch`   | Bug fixes, style tweaks, copy changes — no new functionality |
| `minor`   | New features, new pages, new UI components — backward compatible |
| `major`   | Breaking changes, full redesigns, incompatible API changes |

### Rules

- **Every frontend change** that is committed must bump the version in `frontend/src/version.ts`.
- The version is displayed next to the logo in the top bar so users can confirm which build is deployed.
- Update the version **before** committing (include the bump in the same commit as the change).
- Do **not** bump the version for backend-only changes.

---

## References

- Requirements: `docs/requirements.md`
- Task list: `docs/tasks.md`
- Progress log: `docs/progress.md`
