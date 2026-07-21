# ADR-0010: Adopt loop-engineering safety primitives, not its file layout or score

- **Status:** Proposed
- **Date:** 2026-07-21
- **Deciders:** architect, maintainers
- **Supersedes:** none (extends ADR-0002, ADR-0004, ADR-0009)
- **Superseded by:** none

## Context

As we enable automated phase dispatch (`PHASE_DISPATCH_MODE=oauth|api`) and PR
review (`PR_REVIEW_MODE`), agents increasingly run unattended. This raises
*operational* questions our pipeline does not yet answer: what stops a runaway
loop, what caps spend, what happens when a loop stalls, and where the human
hand-off is.

We evaluated Cobus Greyling's **loop-engineering** framework and its
`loop-audit` CLI (`npx @cobusgreyling/loop-audit .`), which scores a repo's
"Loop Readiness" (0–100, L0–L3). This repo scored **29/100 (L0)**. Two facts
shape how we read that:

1. **loop-audit and its layout are not a de-facto standard.** It is one
   author's recent framework. The score measures conformance to *its* prescribed
   files (`STATE.md`, `loop-run-log.md`, `patterns/registry.yaml`,
   `.foundry/stack.yaml`), not the absolute quality of our design. Chasing the
   number invites Goodhart's law.
2. **Most of what it rewards is documentation of intent, not enforcement.** It
   checks whether `LOOP.md`/`loop-budget.md` *mention* budgets and kill
   switches — prose an LLM is asked to follow, which it can ignore. As ADR-0009
   already states for this project: *written is not enforced.*

The *concepts* it encodes (state persistence, maker/checker split, budget +
kill switch, stall detection, human escalation, least privilege) are, by
contrast, converging industry best practice for autonomous agents and worth
adopting. loop-engineering is deliberately agnostic to *what work* the loop
does, so it does not conflict with our DDD/BDD/SDD/TDD process (ADR-0002): our
phases are the inner loop (making one change correctly); these primitives are
the outer loop (running that safely, unattended). They compose; we keep both.

## Decision

We will **adopt the loop-engineering safety primitives, but not its file
layout, naming, or score.** Concretely:

- We do **not** create `STATE.md`, `loop-run-log.md`, `patterns/registry.yaml`,
  or a Foundry stack, and we do **not** track the loop-audit score. GitHub
  Issues remain the source of truth and `docs/tasks.md` the ephemeral
  scratchpad (ADR-0008); duplicating run/state files would fight that.
- We adopt the primitives, each placed in the layer that gives it the intended
  strength, distinguishing **soft guidance** (prose an agent is asked to follow)
  from **hard enforcement** (harness/CI/billing that actually blocks):

  | Primitive | Soft (guidance) | Hard (enforcement) in this stack |
  | --- | --- | --- |
  | Budget / token cap | `docs` note | Anthropic API key spend limit; CI job timeout |
  | Kill switch | "stop when…" prose | workflow timeout; `settings.json` hooks/permissions blocking tools; human cancel |
  | Stall / no-progress | "escalate after N" prose | wrapper attempt counter + non-zero exit; hook |
  | Least privilege | frontmatter note | Claude Code `permissions` / `allowed-tools` (harness-enforced) |
  | Maker / checker | call `spec-reviewer` by convention | CI merge gate on the reviewer verdict |

- A standing, agent-facing guideline (`docs/`, sibling to `docs/security.md`)
  describes the outer-loop operating rules and **points to** the enforcement
  config, stating plainly which controls are soft and which are hard. The
  guideline alone is soft; only the linked settings/CI/spend-limit layers make a
  control a guarantee.
- The work of moving individual controls into their hard-enforcement layer is
  tracked as **GitHub Issues**, not as TODOs inside docs.

## Consequences

- Easier: unattended dispatch gets an explicit safety envelope; we reuse
  existing assets (`spec-reviewer` as checker, `settings.json`/managed settings
  from ADR-0004, CI gates from ADR-0009) instead of a parallel file tree; the
  soft/hard boundary is stated, so no one mistakes a doc sentence for a guard.
- Harder: each primitive needs real enforcement wiring to be trustworthy; a
  guideline doc plus a set of settings/CI changes is more surface than a single
  `LOOP.md`.
- Explicitly accepted: our loop-audit score stays low because we skip its
  prescribed files. That is intended — we optimise for enforced safety, not the
  score.
- Follow-up (each a GitHub Issue): set an Anthropic spend limit for dispatch
  keys; add job timeouts to the dispatch/review workflows; make the
  `spec-reviewer` verdict a merge gate; add a stall/attempt-cap wrapper with a
  documented escalation exit; audit and tighten `allowed-tools`/`permissions`
  per role; write the `docs/` outer-loop guideline that links them.

## Alternatives considered

- **Conform to loop-engineering fully to raise the score.** Rejected: it is not
  a standard, the score largely measures prose, and its state/run files
  duplicate our Issue-based source of truth (ADR-0008).
- **Replace DDD/BDD/SDD/TDD with loop-engineering.** Rejected on a category
  error: it governs outer-loop operations and is agnostic to the work; our
  pipeline governs inner-loop correctness. Dropping the latter loses what
  ADR-0002 bought us.
- **Write the primitives as guidance only (docs/prompts).** Rejected for the
  same reason as ADR-0009: written is not enforced. Guidance is the floor, not
  the guarantee; controls that must hold are moved to harness/CI/billing.
- **Do nothing until a real incident.** Rejected: automated dispatch is being
  enabled now; the cost of a runaway or unbounded-spend loop is realised before
  any record exists to learn from.
