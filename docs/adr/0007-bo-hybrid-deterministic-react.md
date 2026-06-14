# ADR-0007: BO hybrid deterministic + ReAct architecture (FO pure ReAct)

- **Status:** Accepted (retrospective)
- **Date:** 2026-06-13
- **Deciders:** Architecture team (recorded retrospectively)
- **Supersedes:** none
- **Superseded by:** none

## Context

Recorded retrospectively during the brownfield retrofit. BO triage must handle a
small set of common, well-understood failure causes cheaply and predictably,
while still coping with rare compound or unknown failures. An all-LLM ReAct loop
for every case is expensive and non-deterministic; an all-deterministic approach
cannot handle novel cases.

## Decision

The BO agent (`bo_agent.py`) is a two-tier hybrid graph:

- A deterministic `gather_context_node` sets `triage_path`, and
  `_route_by_triage_path` dispatches known causes to deterministic handlers:
  `AG01` (reactivate counterparty), `MISSING_SSI` (lookup → register or
  escalate), `BE01` (escalate), `AM04` (send back to FO).
- Only `COMPOUND` / `UNKNOWN` causes enter the autonomous
  `deep_investigation_node` (LLM ReAct loop with read tools and HITL write
  tools).

The FO agent (`fo_agent.py`) is a **pure ReAct** loop (router → agent →
tools/END) with HITL on the amend/cancel event nodes. The asymmetry is
deliberate: BO has a well-characterized cause taxonomy worth hard-coding; FO's
work is more open-ended.

## Consequences

- Common BO cases are cheap, fast, and deterministic; the expensive LLM path is
  reserved for genuinely hard cases — this also lowers the model-capability
  requirement (see `docs/ai-driven-development.md` §7 and ADR-0004).
- The deterministic routing is well unit-tested (`test_determine_triage_path`,
  `test_hybrid_routing`); the routing taxonomy must be kept in sync with the
  `RootCause` enum and the glossary.
- Two agent shapes mean two code paths to maintain and reason about.

## Alternatives considered

- **Full ReAct for all BO cases.** Rejected: higher cost and non-determinism for
  failures that have a known, fixed remediation.
- **Fully deterministic BO (no LLM).** Rejected: cannot handle compound/unknown
  causes, which are exactly where investigation value is highest.
