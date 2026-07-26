# ADR-0010: Phase-explicit layout for Gherkin artifacts (features/bdd, features/sdd)

- **Status:** Accepted
- **Date:** 2026-07-26
- **Deciders:** architect, maintainers
- **Supersedes:** none (extends ADR-0002)
- **Superseded by:** none

## Context

The DDD → BDD → SDD → TDD pipeline (ADR-0002) produces two Gherkin artifacts and
a set of Markdown/JSON specs:

| Phase | Artifact | Old path |
| --- | --- | --- |
| BDD | User-facing Gherkin | `features/*.feature` |
| SDD | Detailed, implementable Gherkin | `features/specs/*.spec.feature` |
| SDD | Data-model spec | `docs/specs/*.md` |
| SDD | API contract | `docs/api/openapi.json` |

Two problems made artifact placement ambiguous (issue #68):

1. The name `specs` was used in **two trees** — `features/specs/` (Gherkin) and
   `docs/specs/` (Markdown data-model specs) — same name, different content and
   role.
2. BDD user-facing features and SDD detailed specs were distinguished only by
   folder depth (`features/*` vs `features/specs/*`), so the path alone did not
   make the phase obvious and readers had to consult the docs each time.

## Decision

We will make the path of a Gherkin artifact name its pipeline phase:

- BDD user-facing scenarios live in **`features/bdd/*.feature`**.
- SDD detailed, implementable scenarios live in **`features/sdd/*.spec.feature`**.

`docs/specs/*.md` (the Markdown data-model specs) is left unchanged and is now
the **only** directory named `specs`, so the double-use of the name is gone.
Step definitions continue to live under `tests/bdd/` and are discovered by
pytest via the configured `testpaths`.

This is Option A from issue #68. Option B (renaming `docs/specs/`) and Option C
(keeping folder names but codifying the `.spec.feature` vs `.feature`
convention in prose only) were rejected — see below.

## Consequences

- The path alone tells a human or agent which phase an artifact belongs to; no
  doc lookup is needed to place or find a Gherkin file.
- All references were updated in one pass: the phase skills
  (`.claude/skills/{bdd-feature,sdd-spec,tdd-implement}`), the `spec-reviewer`
  agent, `features/README.md`, `docs/specs/README.md`,
  `docs/ai-driven-development.md`, `docs/governance/review-gates.md`, the issue
  and PR templates, the phase-dispatch workflows, `CODEOWNERS`, and the
  `scenarios(...)` bindings and docstrings in `tests/bdd/`.
- `.github/CODEOWNERS` keeps a single `/features/` rule, which continues to
  cover both `features/bdd/` and `features/sdd/`.
- One-time churn: the git history of the moved files is a rename, and any
  in-flight branch that adds a feature under the old paths must rebase onto the
  new layout.

## Alternatives considered

- **Option B — rename `docs/specs/` (e.g. to `docs/data-model/`).** Also removes
  the name collision, but touches more stable, human-facing documentation paths
  and does not address problem 2 (BDD vs SDD Gherkin distinguished only by
  depth). Rejected in favour of making the two Gherkin phases explicit.
- **Option C — keep folder names, codify the naming convention in prose.** Lowest
  cost, but leaves the duplicated `specs` name and the depth-only distinction in
  place; it documents the confusion instead of removing it. Rejected.
