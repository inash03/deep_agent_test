# CLAUDE.md — Development Rules

This file defines the rules Claude must follow when working in this repository.
Read this file before starting any task.

---

## Development Process

- Work **step by step**; never implement everything at once
- **Clarify requirements** before writing code — ask if anything is unclear
- Define **MVP (Minimum Viable Product)** for new features and **Minimum Viable Change** for bug fixes
- Do **NOT** refactor code unless explicitly instructed
- Do **NOT** add features, helpers, or abstractions beyond what was asked

### At the end of each step:
1. Summarize what was done
2. Propose next steps
3. Update `docs/progress.md`
4. Ask if anything is unclear before proceeding

### Tracking files — keep these up to date:
- `docs/progress.md` — progress log (updated every step)
- `docs/requirements.md` — feature requirements and non-functional requirements
- `docs/tasks.md` — concrete task list (Backlog / In Progress / Done)

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

## References

- Requirements: `docs/requirements.md`
- Task list: `docs/tasks.md`
- Progress log: `docs/progress.md`
