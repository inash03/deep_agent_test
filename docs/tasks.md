# Agent Scratchpad

This file is the **working memory for the current branch/agent session** — a
scratchpad, not shared task state.

- **Source of truth for tasks is GitHub Issues / Projects** (one Issue = one
  feature = one branch = one session). See `docs/ai-driven-development.md` §5 and
  ADR-0002 / ADR-0008. Do **not** record backlog or cross-session state here.
- This file is **ephemeral**: safe to overwrite or clear when starting new work.
  It is not an audit trail — git history and the Issue/PR timeline are.
- Use it for the plan, intermediate findings, and the next concrete step while
  working a single Issue.

## Current Issue

#69 — Issue-creation tooling: auto-generate DDD/BDD/SDD/TDD sub-issues under a
parent, and feed parent+child into each phase. Branch `claude/issue-69-ddd-73xxyi`.

## Plan

1. DDD: assess whether the feature introduces a new business-domain concept.
2. If "no change", get architect (user) sign-off, then continue to BDD/SDD/TDD
   in this same session (agreed with user — this is peripheral tooling, not a
   business feature, so per-phase session isolation is not required).
3. BDD phase revealed a structural mismatch: `features/*.feature` +
   `tests/bdd/` requires binding to real domain/application code, but this
   Issue's deliverable is skill/template/doc files only (no app code). User
   chose to simplify the pipeline: skip formal Gherkin/pytest-bdd, treat the
   Issue's acceptance criteria as the Definition of Done, implement directly,
   PR review as the gate.
4. Implemented all 6 acceptance-criteria items directly (see below). Ran
   `uv run pytest` as the applicable completion-gate check (no frontend files
   touched, so `npm run lint`/`build` not applicable).

## Notes / findings

- Issue #69 scope: `.claude/skills/*`, `.github/ISSUE_TEMPLATE/`,
  `docs/ai-driven-development.md`. All owned by "process / agent control
  files" in CODEOWNERS, not `/docs/domain/`.
- `docs/domain/glossary.md` is explicitly scoped to the **STP Exception
  Triage business domain** (trades, counterparties, triage, HITL, etc.).
  "Parent issue" / "sub-issue" / "phase skill" are software-development-process
  concepts already defined in `docs/ai-driven-development.md` (§4, §5), not
  business-domain concepts.
- Verdict: **no change** to `docs/domain/glossary.md`, `model.md`, or
  `context-map.md`. This feature does not introduce or alter a business
  concept — it changes how Issues are filed and how phase skills read their
  inputs, which is process tooling.
- No conflict/synonym found (no glossary term overlaps with "parent issue" /
  "sub-issue" / "phase skill").

## Design revision — hybrid filing (user decision)

User chose a **hybrid** split instead of the agent filing all 5 issues:
- Parent feature Issue: authored by the `/feature-issue` agent skill
  (feature-specific reasoning: story translation + acceptance criteria).
- Four DDD/BDD/SDD/TDD sub-issues: created **mechanically by a GitHub Action**
  (`create-phase-subissues`) on parent creation — boilerplate, deterministic,
  zero tokens, and the open/closed state is the phase-completion tracker.

Rationale: the sub-issue content is fixed boilerplate that duplicates the
phase skills, so an agent adds no quality there; determinism/reliability wins.

## Implementation (hybrid)

- NEW `.github/workflows/create-phase-subissues.yml` — Action (github-script)
  fires on issue opened/labeled with `feature`, idempotent, creates + links 4
  sub-issues via the sub-issues REST API (`sub_issue_id` = child `id`), posts
  a summary comment. Sub-issues labelled `phase-subissue` (no recursion).
- REWROTE `.claude/skills/feature-issue/SKILL.md` — parent Issue only; Action
  owns sub-issues; keeps draft-then-approve + English rule.
- `.github/ISSUE_TEMPLATE/feature.yml` + `phase-subissue.yml` — notes updated
  to reference the Action; phase-subissue form is now a manual fallback.
- 4 phase skills — input wording decoupled from `/feature-issue`
  ("if the feature has phase sub-issues") + single-Issue fallback retained.
- `docs/ai-driven-development.md` — §5 rewritten as hybrid, §6/§9/§10 updated.

## Verification

- YAML valid (workflow + 2 templates).
- github-script JS passes `node --check` (wrapped as an async fn, as the
  action does).
- `uv run pytest` unaffected (no Python touched); pre-existing unrelated
  `pytest-archon` collection gap in `tests/unit/test_architecture.py` remains
  (optional extra, not installed by plain `uv sync`).

## Next step

Commit + push to `claude/issue-69-ddd-73xxyi`. The Action can only be
exercised end-to-end once merged (needs to run on GitHub); locally validated
by static checks.
</content>
