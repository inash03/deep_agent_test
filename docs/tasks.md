# Task List

This file tracks concrete implementation tasks.
Updated by Claude at the end of each development step.

Status: `[ ]` Backlog · `[~]` In Progress · `[x]` Done

---

## Done

- [x] Development rules setup (CLAUDE.md, progress.md, requirements.md, tasks.md)

---

## Backlog

### Phase 1 — Project Scaffolding

- [ ] Create `pyproject.toml` with pinned dependencies (LangGraph, FastAPI, Pydantic, pytest, ruff, mypy)
- [ ] Create `src/` directory structure (`presentation/`, `domain/`, `infrastructure/`)
- [ ] Create `__init__.py` files for each package
- [ ] Create `.env.example` with required key names (e.g. `ANTHROPIC_API_KEY=`)
- [ ] Verify `.env` is in `.gitignore`
- [ ] Create `tests/unit/` and `tests/integration/` directories

### Phase 2 — First Agent (MVP)

- [ ] Clarify MVP agent requirements with user
- [ ] Implement domain layer: agent use case interface and entity definitions
- [ ] Implement infrastructure layer: LangGraph `StateGraph` agent with at least one tool
- [ ] Implement presentation layer: FastAPI router + Pydantic request/response schemas
- [ ] Wire up layers with dependency injection
- [ ] Manual smoke test via FastAPI `/docs`

### Phase 3 — Testing

- [ ] Write unit tests for domain layer
- [ ] Write integration test for agent endpoint
- [ ] Configure `pytest` in `pyproject.toml`

### Phase 4 — Observability

- [ ] Add structured logging for agent step-by-step execution
- [ ] Return intermediate steps in API response (optional field)

---

## In Progress

*(none)*
