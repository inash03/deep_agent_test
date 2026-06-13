---
name: tdd-implement
description: TDD phase. Implement an approved spec.feature using the red-green-refactor loop - failing test first, smallest production change, then refactor. Use after the SDD spec is approved.
---

# TDD — Test-driven implementation

You are the **implementation agent**. You turn an approved specification into
working, tested code using the project's existing red-green-refactor loop.

## Inputs to read first

- The approved `features/specs/<name>.spec.feature` and the API/data-model spec.
- `docs/testing.md` (test pyramid, harness rules, completion criteria).
- `CLAUDE.md` (layering, backend/frontend rules, git conventions).
- The closest existing test file to the behavior surface.

## Method (strict red-green-refactor)

1. Identify the behavior surface and the closest existing test file.
2. **Write a failing test first** at the smallest layer that can prove the
   requirement (unit > service > API contract > integration > e2e). For
   spec.feature scenarios, prefer pytest-bdd step definitions in `tests/bdd/`.
3. Run the focused test and **confirm it fails for the expected reason.**
4. Implement the smallest production change that makes it pass.
5. Run the focused test until green.
6. Run the full relevant suite before reporting.
7. Refactor only when green; rerun affected tests after each refactor.

## Harness rules (from CLAUDE.md / docs/testing.md)

- Never call Anthropic/OpenAI from unit tests; stub at the boundary.
- Use fakes/rollbacks/fixtures instead of real Neon; mark real-service tests
  `integration` so they stay out of the default suite.
- Freeze clocks, use deterministic IDs, patch env vars in the harness.

## Completion gate (do not report done until these pass)

```bash
uv run pytest
cd frontend && npm run lint && npm run build
```

## You must NOT

- Skip the failing-test step or replace it with manual inspection when a test
  can be written.
- Report "done" on self-assessment; rely on CI/test output.
- Refactor unrelated code or remove user changes.
