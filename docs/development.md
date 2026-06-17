# Development Guide

How to work in this repository: the development process, task tracking, the
end-of-step checklist, git conventions, and the useful commands. Testing rules
live in `docs/testing.md`; the AI-driven phase pipeline lives in
`docs/ai-driven-development.md`.

## Development Process

- Keep changes scoped to the requested task.
- Prefer existing patterns over new abstractions.
- Do not refactor unrelated code.
- Do not remove user changes.
- Update documentation when architecture, environment variables, endpoints, or
  deployment behavior changes.
- Use test-driven development for every behavior change (see `docs/testing.md`).
  Write or update the smallest meaningful test before implementing production
  code.
- Do not report a task as complete until the relevant automated checks pass
  100%, or until a blocker is clearly documented with the exact failing command
  and failure reason.

## Task Tracking

The source of truth for tasks is **GitHub Issues / Projects** — one Issue = one
feature (or scenario group) = one branch = one agent session (ADR-0002,
ADR-0008). Track state, ownership, priority, and history there, not in Markdown.

`docs/tasks.md` is an **ephemeral per-session scratchpad** (working memory for
the current branch): the plan, intermediate findings, and the next step. It is
safe to overwrite or clear, and is not shared, cross-session state.

## End-of-Step Checklist

1. Run relevant checks until they pass 100%.
2. Update docs if behavior, architecture, env vars, or deployment changed.
3. Update the GitHub Issue/PR (status, checklist, links) — that is the audit
   trail, not a Markdown log.
4. Summarize changes and verification for the user, including exact commands
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

# Architecture fitness functions (see docs/governance/automated-gates.md)
uv run lint-imports            # import-linter contracts
uv run pytest -m architecture  # pytest-archon rules (excluded from default suite)

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
</content>
