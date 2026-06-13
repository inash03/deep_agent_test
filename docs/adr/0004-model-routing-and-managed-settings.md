# ADR-0004: Model routing per phase and managed settings

- **Status:** Accepted
- **Date:** 2026-06-13
- **Deciders:** Architecture team
- **Supersedes:** none
- **Superseded by:** none

## Context

Phase 3 of the AI-driven development process (ADR-0002) adds subagents, AI code
review, model routing, and managed settings. Two decisions need recording:
(1) which model to use in which phase, given that the target deployment may only
have an Opus-level model (no frontier model); and (2) how to enforce hard
prohibitions that must not be overridable by an individual operator.

## Decision

**Model routing.** Match model strength to the leverage of the work:

| Work | Model | Rationale |
| --- | --- | --- |
| DDD / SDD design judgement | strongest available (Opus-level) | High-leverage; ambiguity here is expensive downstream. |
| AI code review (`spec-reviewer`, the review workflow) | strongest available (Opus-level) | Independent second pass must catch subtle errors. |
| TDD routine implementation (spec locked) | cheaper (Sonnet-level) | A detailed spec lowers the model requirement. |
| Read-only research / search (`researcher`) | cheaper (Sonnet/Haiku-level) | Mechanical; cost-sensitive. |

Routing is encoded concretely in the `model:` field of `.claude/agents/*.md` and
the `--model` arg in `.github/workflows/claude-review.yml`. This is also the
non-frontier-model strategy: thicker specs plus an independent review pass
compensate for a weaker implementation model (see `docs/ai-driven-development.md`
§7).

**Managed settings.** Hard prohibitions are shipped as managed (organization or
system) settings that an individual cannot override, separate from the shared
project `.claude/settings.json` (which holds the convenience permission
allowlist). Prohibitions to enforce centrally: no direct push to `main`
(branch protection), never commit secrets, agents must not run arbitrary shell,
and deny destructive commands. The committed `.claude/settings.json` is for
shared convenience only and is intentionally free of behavior-changing hooks.

## Consequences

- Subagent and workflow model choices are explicit and reviewable in-repo.
- Cost drops because routine implementation and search do not use the top model.
- Managed settings live outside this repository (org/system policy), so this ADR
  records the intent; the repo ships only the safe shared allowlist.
- Model identifiers in config will need occasional updates as models change.

## Alternatives considered

- **One model for everything.** Rejected: either overpays for routine work or
  underpowers design/review.
- **Enforce prohibitions only via project `.claude/settings.json`.** Rejected:
  project settings can be edited in a PR by anyone; hard prohibitions belong in
  managed settings that are not locally overridable.
