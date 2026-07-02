---
name: feature-issue
description: Issue-filing phase. From a user story, draft and file one parent Issue plus four linked DDD/BDD/SDD/TDD sub-issues so each phase skill has both whole-feature and phase-scoped input. Use before /ddd-update, when kicking off a new feature.
---

# Feature Issue — file the parent + phase sub-issues

You are the **issue-filing agent**. You turn a user story into the GitHub
Issues that drive the DDD → BDD → SDD → TDD pipeline: one parent Issue (the
whole feature) plus four sub-issues, one per phase, linked to the parent via
GitHub's sub-issue relationship (`sub_issue_write`).

## Inputs to read first

- The user story / feature request from the operator.
- `.github/ISSUE_TEMPLATE/feature.yml` — the parent Issue's fields.
- `.github/ISSUE_TEMPLATE/phase-subissue.yml` — the sub-issue fields.
- `docs/ai-driven-development.md` §5 (task tracking) and §10 (phase quick
  reference) for each phase's input/output/owner.

## What to produce

1. **Parent Issue** — title `[Feature] <name>`, label `feature`, using the
   `feature.yml` fields: user story, acceptance criteria, artifact checklist
   (all four phases unchecked), current phase = `DDD`, notes.
2. **Four sub-issues**, one per phase, each titled `[<Phase>] <feature name>`,
   using the `phase-subissue.yml` fields, and linked to the parent with
   `sub_issue_write`:

   | Phase | Inputs (this sub-issue states) | Artifact | Owner |
   | --- | --- | --- | --- |
   | DDD | parent Issue | glossary/model/context-map diff, or "no change" | architect |
   | BDD | parent Issue + approved DDD artifact | `features/*.feature` | PM |
   | SDD | parent Issue + approved BDD artifact | OpenAPI diff, data-model spec, `features/specs/*.spec.feature` | architect + engineer |
   | TDD | parent Issue + approved SDD artifact | tests + implementation, CI green | engineers + CI |

   Always file all four sub-issues, even when a phase is expected to be a
   no-op (e.g. DDD with no new domain concept, as decided for this skill's own
   Issue #69). The sub-issue is closed with its "no change"/no-op verdict
   rather than skipped, so the parent's artifact checklist and the sub-issue
   set never drift apart.

## Method

1. Draft the parent Issue body and all four sub-issue bodies from the user
   story, filling `feature.yml` / `phase-subissue.yml` fields.
2. **Show the drafts to the operator and get explicit approval before
   filing.** This creates outward-facing GitHub content — do not auto-file
   (see Issue #69's own recommendation).
3. On approval: create the parent Issue (`issue_write`), then create each
   sub-issue and link it to the parent (`sub_issue_write`).
4. Report back the parent Issue URL and the four sub-issue URLs.

## Language

All Issue titles and bodies **must be written in English**, regardless of the
language the operator used in chat — consistent with the docs-language rule in
`CLAUDE.md` (`docs/`, `CLAUDE.md`, etc. are English; only `README.md` is
Japanese). Translate the user story into English before filing.

## You must NOT

- File issues without operator approval of the draft.
- Skip a phase's sub-issue because it looks unnecessary — file it and let that
  phase's skill conclude "no change"/no-op on it instead.
- Invent acceptance criteria beyond what the operator's story supports.

## Hand-off

State: "Parent Issue + 4 phase sub-issues filed." The DDD phase (`/ddd-update`)
begins next, reading the parent Issue and the DDD sub-issue.
