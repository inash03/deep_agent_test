# Review gates — making the phase hand-offs enforceable (HITL → HOTL)

Companion to `docs/governance/automated-gates.md`. That document covers
*machine* checks; this one covers the *human and AI review gates* between the
DDD → BDD → SDD → TDD phases, and how to make them real instead of advisory.

## The problem this fixes

The phase hand-offs in `docs/ai-driven-development.md` ("ready for architect
review", "approved via PR before the next phase") are **prose, not
enforcement**. `.github/CODEOWNERS` only requests reviewers **when a PR is
opened**, and only blocks **merge** (not an agent's progression) **if branch
protection requires it**. Consequence: a single agent running the phase skills
back-to-back on one branch, with no per-phase PR, passes through every gate
without a human ever stopping it.

Separately, the mechanical CI checks (pytest, OpenAPI drift, architecture
contracts) can all be green while a **semantic** defect slips through. This was
demonstrated on this very repo: an independent `spec-reviewer` pass caught that a
new engine rule (`value_date_not_weekend`) was added to `FO_RULES` but not to the
hand-written dashboard registry (`GET /api/v1/rules`, FR-10) — invisible to
operators, and uncatchable by the OpenAPI drift test (the gap is in response
*data*, not schema).

So the pipeline needs **two enforcement layers**, not one:

1. **Human gate (HITL)** — irreducible product/architecture judgment, enforced
   by CODEOWNERS + branch protection on per-phase PRs.
2. **Automated semantic gate (toward HOTL)** — an independent AI review and
   consistency fitness functions, so humans approve by *exception* rather than
   reading every artifact in full.

## Operating model: one PR per phase

Each phase produces one small PR whose diff is the reviewable unit. Merge is
blocked until the required checks pass **and** the CODEOWNER approves.

| Phase | Artifact (PR scope) | CODEOWNER (from `.github/CODEOWNERS`) | Automated checks that gate it |
| --- | --- | --- | --- |
| DDD | `docs/domain/*` | architect | (planned) glossary-term lint |
| BDD | `features/*.feature` + `tests/bdd/` | PM | pytest-bdd executes; no orphan steps |
| SDD | `docs/api/`, `docs/specs/`, `features/specs/*` | architect + engineer | OpenAPI drift test |
| TDD | `src/**`, `tests/**` | engineer + CI | full suite, architecture fitness, dashboard-sync, AI review |

Running everything in one branch/agent (as in the pipeline demo) is fine for a
*spike*, but the real workflow splits the phases so each gate has something to
stop on.

## B — Turn on the human gate (branch protection)

CODEOWNERS already routes reviews; it only *enforces* once branch protection on
`main` requires it. Apply in **Settings → Branches → Add rule** (or a Ruleset):

- Require a pull request before merging; **require 1 approval**.
- **Require review from Code Owners** (this is what activates CODEOWNERS).
- Dismiss stale approvals when new commits are pushed.
- **Require status checks to pass** — select the **`backend-tests`** job. The
  architecture fitness functions and the dashboard-sync test already run inside
  that job (`uv run pytest`), so requiring it enforces them too.
- Require branches to be up to date before merging.
- Include administrators (no silent bypass).

This is a repository setting and cannot be toggled from the coding environment.
Apply via the UI above, or the API:

```bash
# requires admin token; illustrative
gh api -X PUT repos/inash03/deep_agent_test/branches/main/protection \
  -f required_pull_request_reviews.require_code_owner_reviews=true \
  -f required_pull_request_reviews.required_approving_review_count=1 \
  -f required_status_checks.strict=true \
  -f 'required_status_checks.checks[][context]=backend-tests' \
  -f enforce_admins=true -f restrictions=
```

## C — Turn on the automated semantic gate (independent AI review)

This is the highest-leverage step for reducing human approval load, because it
attacks the *semantic* gap the mechanical checks cannot.

- **In CI:** `.github/workflows/claude-review.yml` already runs an independent,
  spec-conformance review on every PR, gated on the `ANTHROPIC_API_KEY` secret.
  Activate it: **Settings → Secrets and variables → Actions → New repository
  secret** `ANTHROPIC_API_KEY`, and install the Claude GitHub App
  (`https://github.com/apps/claude`). Until the secret exists the job skips and
  stays green, so nothing is blocked in the meantime.
- **In-session / pre-push:** run the `spec-reviewer` subagent (`.claude/agents/`)
  against the working diff. It is read-only and returns Blocking / Should-fix /
  Nits with a verdict. This is the pass that caught the dashboard desync above.

## Promote every finding to a check

When a reviewer (human or AI) catches a *class* of defect, encode it so nobody
reviews for it by hand again — the core HOTL mechanic. Worked example from this
repo: the rules-dashboard desync → `tests/unit/test_rules_dashboard_sync.py`
(asserts every engine rule appears on the dashboard with a matching severity).
Each such promotion permanently removes a line item from human review.

## What stays human

Do not try to automate away product and architecture judgment. Keep a required
human approval on **DDD/domain** changes and **ADRs**. As automated coverage
grows (contract drift, architecture, dashboard-sync, independent AI review),
*reduce* the required human approvals on TDD-level PRs toward exception-handling
— that shift, not the removal of all review, is the HOTL goal.
</content>
