# Feature files (BDD)

This directory holds the executable behavior specifications for the project,
written in Gherkin. They are the **BDD** artifact in the AI-driven development
pipeline (see `docs/ai-driven-development.md`).

## Rules

- **Every `.feature` file here is executed in CI.** Gherkin that is not executed
  rots and stops being trusted. A feature with no step definitions is a bug, not
  a draft.
- Step definitions live under `tests/bdd/` (so pytest discovers them via the
  configured `testpaths`) and call real domain/application code with the project
  harness rules in `docs/testing.md` (no real LLM, DB, or network in the default
  suite).
- Business-facing scenarios use the ubiquitous language in
  `docs/domain/glossary.md`. The PM reviews these files in the PR.

## Layout

```
features/
  *.feature              # BDD: user-facing scenarios (PM-reviewed)
  specs/*.spec.feature   # SDD: detailed, implementable scenarios incl. errors (added in Phase 2)
```

## Running

```bash
# Run only the BDD scenarios
uv run pytest tests/bdd -v

# Or as part of the full default suite
uv run pytest
```

## Authoring with the agent

Use the `/bdd-feature` skill to draft a feature from a user story, then the
`/sdd-spec` skill to derive the detailed `spec.feature`. A human owner reviews
each before it flows to the next phase.
