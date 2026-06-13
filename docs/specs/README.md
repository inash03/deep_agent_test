# Specifications (SDD)

This directory holds the **data-model and behavior specifications** produced in
the SDD phase (see `docs/ai-driven-development.md`). A spec here is the precise,
implementable contract derived from an approved BDD feature.

Each feature's spec set is:

- **API contract** — `docs/api/openapi.json` (the endpoint contract, drift-tested).
- **Data-model spec** — `docs/specs/<feature>.md` (this directory): tables,
  fields, constraints, and error mapping, in Markdown.
- **Detailed scenarios** — `features/specs/<feature>.spec.feature`: boundary and
  error cases, executed in CI via step definitions in `tests/bdd/`.

The governing rule still applies: do not write a specification that CI does not
execute or verify. Data-model specs are kept in sync with Alembic migrations and
the domain enums in `src/domain/entities.py`.
