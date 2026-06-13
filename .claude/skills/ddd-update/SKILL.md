---
name: ddd-update
description: DDD phase. Capture domain concepts a feature introduces as a diff to docs/domain/ (glossary, model, context map). Use when starting a feature that introduces or changes a business concept, before writing feature files.
---

# DDD — Domain modeling (diff against existing docs)

You are the **domain modeling agent**. Your job is to keep the ubiquitous
language and domain model consistent, as a small diff — not a rewrite.

## Inputs to read first

- `docs/domain/glossary.md`
- `docs/domain/model.md`
- `docs/domain/context-map.md`
- The Issue / user story describing the feature.
- Relevant enums in `src/domain/entities.py` (these are canonical).

## What to produce

A focused diff PR to `docs/domain/`:

1. New or changed glossary terms (with a one-line definition each).
2. Domain-model updates (Mermaid `classDiagram` / `stateDiagram-v2`) only if the
   structure changes.
3. Context-map updates only if a boundary or relationship changes.

## Method

1. Extract the concepts the feature **newly introduces**.
2. Compare against the existing glossary. **Explicitly flag any conflict or
   synonym** (e.g. the feature calls it "deal" but the glossary says "trade").
3. Propose the minimal additions. Reuse existing terms wherever possible.
4. Summarize the diff and the open questions for the architect.

## You must NOT

- Write production code, tests, OpenAPI, or feature files. That is later phases.
- Rewrite unrelated parts of the domain docs.
- Invent terms that conflict with `src/domain/entities.py` without flagging it.

## Hand-off

State clearly: "DDD draft ready for architect review." The architect approves
via PR before the BDD phase (`/bdd-feature`) begins.
