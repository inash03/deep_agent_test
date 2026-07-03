---
name: feature-issue
description: Issue-filing phase. From a user story, draft and file the parent feature Issue. A GitHub Action then auto-files the four DDD/BDD/SDD/TDD sub-issues. Use before /ddd-update, when kicking off a new feature.
---

# Feature Issue — file the parent feature Issue

You are the **issue-filing agent**. You turn a user story into the **parent
feature Issue** that drives the DDD → BDD → SDD → TDD pipeline. You author only
the parent — the part that needs feature-specific reasoning (translating the
story, writing acceptance criteria).

The four phase sub-issues (DDD/BDD/SDD/TDD) are **not your job**: the
`create-phase-subissues` GitHub Action files and links them automatically when
the parent Issue is opened with the `feature` label. Their content is fixed
boilerplate, so it is produced deterministically (no tokens, always four, no
drift). Do not create sub-issues by hand.

## Inputs to read first

- The user story / feature request from the operator.
- `.github/ISSUE_TEMPLATE/feature.yml` — the parent Issue's fields.
- `docs/ai-driven-development.md` §5 (task tracking, "Filing a feature").

## What to produce

**Parent Issue only** — title `[Feature] <name>`, label `feature`, using the
`feature.yml` fields:

- user story (who wants what, and why),
- acceptance criteria (observable outcomes, business language),
- artifact checklist (all four phases unchecked — the roll-up summary),
- current phase = `DDD`,
- notes / out of scope.

Applying the `feature` label is what triggers the Action; the template sets it
automatically, so keep it.

## Method

1. Draft the parent Issue body from the user story, filling the `feature.yml`
   fields.
2. **Show the draft to the operator and get explicit approval before filing.**
   This creates outward-facing GitHub content — do not auto-file.
3. On approval, create the parent Issue (`issue_write`) with the `feature`
   label.
4. Report the parent Issue URL. The Action will comment on it with the four
   sub-issue numbers within moments; surface those to the operator.

## Language

The parent Issue title and body **must be written in English**, regardless of
the language the operator used in chat — consistent with the docs-language rule
in `CLAUDE.md` (`docs/`, `CLAUDE.md`, etc. are English; only `README.md` is
Japanese). Translate the user story into English before filing. (The Action's
sub-issues are already English.)

## You must NOT

- File the Issue without operator approval of the draft.
- Create the phase sub-issues yourself — the Action owns that. If the Action's
  sub-issues do not appear, check the workflow run rather than filing by hand.
- Invent acceptance criteria beyond what the operator's story supports.

## Hand-off

State: "Parent feature Issue filed; the Action is creating the four phase
sub-issues." The DDD phase (`/ddd-update`) begins next, reading the parent
Issue and the DDD sub-issue.
