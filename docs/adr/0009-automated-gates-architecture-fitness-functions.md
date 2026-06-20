# ADR-0009: Convert pipeline gates into enforced fitness functions; adopt architecture checks

- **Status:** Accepted
- **Date:** 2026-06-16
- **Deciders:** architect, maintainers
- **Supersedes:** none (extends ADR-0002, ADR-0003)
- **Superseded by:** none

## Context

The DDD/BDD/SDD/TDD pipeline relies on human review at each phase (HITL). Human
review is the rate-limiting step and, with agents writing both code and tests,
"the suite is green" is a weakening signal: a test written by the same agent can
be tautological or coupled to the implementation, and automated checks only ever
verify what someone already thought to specify — not the unspecified negative
space where risk lives.

We want to move toward Human-on-the-Loop (HOTL): humans own the highest-level
rules and supervise, while the conformance checks they used to perform by eye
are encoded as machine-enforced checks. The codebase already has one such check
(the OpenAPI drift test, ADR-0003). It has a layered package structure
(`domain`/`infrastructure`/`presentation`) whose Clean Architecture rules are
currently conventions, not gates.

## Decision

We will treat **automated, enforced checks ("fitness functions") as the primary
gate** and human review as the discovery mechanism for new checks, rolled out
**advisory → backlog burndown → blocking**. The roadmap and the full gate→check
map live in `docs/governance/automated-gates.md`.

As the first increment we adopt **architecture fitness functions** using both a
declarative and an ArchUnit-style engine:

- **import-linter** (`.importlinter`): `domain-purity` (domain free of
  frameworks/I/O) and `layers` (`presentation → infrastructure → domain`).
- **pytest-archon** (`tests/unit/test_architecture.py`, marker `architecture`):
  domain independence and framework-freedom.

Both pass today and are wired **advisory** in CI (`continue-on-error: true`).
A single type-only Clean Architecture leak
(`src.domain.check_rules -> src.infrastructure.db.models` under `TYPE_CHECKING`)
is recorded as accepted debt via whitelists rather than hidden.

## Consequences

- Easier: architecture rules become machine-checked and catch the next
  violation automatically; review effort shifts to designing checks; the debt
  (application layer fused into `infrastructure`) is now explicit.
- Harder: contributors must keep contracts green or update them deliberately;
  new tooling (`import-linter`, `pytest-archon`) in dev deps and CI.
- Follow-up (tracked in `docs/governance/automated-gates.md` and Issue #55):
  flip these checks to blocking; extract `src/application`; invert the
  `check_rules` type dependency and drop the whitelists; add mutation testing,
  security audits, Spectral/schemathesis, and provenance-linkage checks.

## Alternatives considered

- **Keep architecture rules as written conventions (ADR/docs only).** Rejected:
  "written" is not "enforced"; conventions rot and agents do not obey them.
- **Make the checks blocking immediately.** Reasonable since they are green, but
  rejected for the first landing to keep the rollout uniform with ruff and to
  let contributors absorb the new tooling; flipping to blocking is a one-liner.
- **Pick a single architecture tool.** Rejected for now: import-linter gives
  declarative layer/direction contracts while pytest-archon gives pytest-native
  rules; using both keeps the boundary expressible in either style.
- **Disable indirect-import detection to make domain-purity pass.** Rejected:
  indirect detection is the stronger guarantee; we whitelist the one known
  type-only edge instead.
</content>
