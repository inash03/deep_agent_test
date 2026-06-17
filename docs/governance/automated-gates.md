# Automated Gates — converting human review into enforced checks

This document is the roadmap for moving the DDD/BDD/SDD/TDD pipeline from
**Human-in-the-Loop (HITL)** toward **Human-on-the-Loop (HOTL)**: human review
ceases to be the in-line, per-change bottleneck and becomes oversight, while the
correctness/conformance checks humans used to perform by eye are turned into
**machine-enforced checks** ("fitness functions").

Decision record: ADR-0009. Related: `docs/ai-driven-development.md` (the
pipeline), ADR-0002 (Issues as source of truth), ADR-0003 (OpenAPI drift test —
the first fitness function in this repo).

## Principles

1. **Convert gates, don't remove review.** Every human gate becomes an enforced
   check (the "judiciary"). Review survives as the *discovery lab for new
   checks*, not as the gate. When a reviewer catches a class of defect, promote
   it to an automated check so nobody reviews for it by hand again.
2. **Independence.** A test written by the same agent that wrote the code
   inherits that agent's blind spots. Verification must be independent: a
   different model/reviewer (`spec-reviewer`), mutation testing, and
   property/fuzz testing that probe the *negative space* — the inputs nobody
   thought to specify.
3. **SSOT vs derived data.** Only human-approved originals (requirements, domain
   rules, contracts, tests) are valid grounds for a decision. Machine-generated
   artifacts (dependency graphs, impact analyses) are navigation/index only.
4. **Staged rollout.** Each check lands **advisory → backlog burndown →
   blocking**, the same path ruff is on. A check is never introduced as blocking
   on a red codebase (that just gets it disabled).

## Gate → check map

| Pipeline stage | Current human gate | Enforced check (judiciary) | Tooling | Status |
| --- | --- | --- | --- | --- |
| DDD | architect approves glossary diff | new domain terms must exist in glossary; CODEOWNERS on `docs/domain/` | custom lint + CODEOWNERS | planned |
| BDD | PM approves feature | features execute in CI; no undefined/pending steps; Issue link | pytest-bdd (done) | partial |
| SDD | architect/eng approve contract | OpenAPI drift (done); OpenAPI lint; contract fuzz | spectral, schemathesis | planned (#54) |
| TDD: structure | reviewer eyeballs design | dependency direction, layer purity, no cycles, complexity | **import-linter + pytest-archon** (this increment), radon/xenon | **advisory** |
| TDD: test quality | trust "green" | mutation testing kills tautological tests; property-based for negative space | mutmut/cosmic-ray, Hypothesis | planned |
| TDD: security | ad hoc | dependency audit, SAST, secret scan | pip-audit, npm audit (#57), bandit, gitleaks | planned |
| Cross-cutting | human review | independent AI reviewer (different model) | `spec-reviewer`, claude-review (#54) | partial |
| Cross-cutting | memory links rule↔check↔test | requirement↔spec↔test linkage check | machine-readable coverage matrix | planned |

## Architecture fitness functions (this increment)

Both an ArchUnit-style engine and a declarative one are wired, per the chosen
"use both" approach:

- **import-linter** — declarative contracts in `.importlinter`, run with
  `uv run lint-imports`. Enforces:
  - `domain-purity`: `src.domain` must not depend on frameworks/I/O (fastapi,
    sqlalchemy, langgraph, langchain, httpx, …), including transitively.
  - `layers`: dependency direction `presentation → infrastructure → domain`.
- **pytest-archon** — pytest-native rules in `tests/unit/test_architecture.py`,
  run with `uv run pytest -m architecture`. Asserts domain independence and
  framework-freedom (`skip_type_checking=True`).

Both are **green today** and wired as **advisory** in CI only to honor the
staged rollout. Because they pass, flipping them to blocking is a one-line
change (`continue-on-error: false`) and is recommended.

### Recorded architecture debt (a fitness-function finding)

The checks surfaced a real Clean Architecture leak, recorded as accepted debt
rather than hidden:

- `src.domain.check_rules` imports `src.infrastructure.db.models` under
  `if TYPE_CHECKING:` (type-only), which transitively reaches sqlalchemy. It is
  whitelisted via `ignore_imports` in `.importlinter` and `skip_type_checking`
  in the pytest-archon rule.
- **Bigger finding:** use cases and agents (`fo_triage_use_case.py`,
  `bo_triage_use_case.py`, `bo_agent.py`, …) live under `src/infrastructure/`,
  i.e. the application layer is fused into infrastructure. Extracting a
  `src/application` layer and inverting the `check_rules` type dependency
  (move the referenced types into the domain) is tracked as a Retrofit sub-task
  (Issue #55). When done, add the stricter target contract
  `presentation → application → domain`, `infrastructure → domain` (DIP) and
  remove the two whitelist entries.

## Commands

```bash
uv run lint-imports              # import-linter contracts
uv run pytest -m architecture    # pytest-archon fitness functions
uv run pytest                    # default suite (excludes integration + architecture)
```

## Next increments

1. Make import-linter + pytest-archon **blocking** (they already pass).
2. Mutation testing pilot (mutmut) on `src/domain` to quantify test strength and
   catch tautological AI-written tests; later gate on a mutation-score floor.
3. Security fitness functions: `pip-audit`, `npm audit` (#57), `bandit`,
   `gitleaks` — advisory first.
4. OpenAPI: Spectral lint + schemathesis fuzz (#54).
5. Extract `src/application`, add the DIP target contract, drop the whitelists.
6. Machine-readable Specification Provenance: link requirement ↔ spec ↔ test so
   an agent can detect (and stop on) broken linkage.
</content>
