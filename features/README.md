# Feature files (BDD + SDD Gherkin)

This directory holds the executable Gherkin specifications for the project. The
path tells you which phase an artifact belongs to:

- `features/bdd/*.feature` — the **BDD** artifact: user-facing behavior scenarios
  (PM-reviewed).
- `features/sdd/*.spec.feature` — the **SDD** artifact: detailed, implementable
  scenarios including boundary and error cases (added in the SDD phase).

See `docs/ai-driven-development.md` for the full pipeline. The Markdown
data-model specs produced in the SDD phase live separately under `docs/specs/`.

## Rules

- **Every Gherkin file here is executed in CI**, whether under `bdd/` or `sdd/`.
  Gherkin that is not executed rots and stops being trusted. A feature with no
  step definitions is a bug, not a draft.
- Step definitions live under `tests/bdd/` (so pytest discovers them via the
  configured `testpaths`) and call real domain/application code with the project
  harness rules in `docs/testing.md` (no real LLM, DB, or network in the default
  suite).
- Business-facing scenarios use the ubiquitous language in
  `docs/domain/glossary.md`. The PM reviews these files in the PR.

## Layout

```
features/
  bdd/*.feature        # BDD: user-facing scenarios (PM-reviewed)
  sdd/*.spec.feature   # SDD: detailed, implementable scenarios incl. errors (added in Phase 2)
```

## Running

```bash
# Run only the BDD/SDD Gherkin scenarios
uv run pytest tests/bdd -v

# Or as part of the full default suite
uv run pytest
```

## Authoring with the agent

Use the `/bdd-feature` skill to draft a feature under `features/bdd/` from a user
story, then the `/sdd-spec` skill to derive the detailed `features/sdd/*.spec.feature`.
A human owner reviews each before it flows to the next phase.
