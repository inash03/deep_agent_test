# Glossary (Ubiquitous Language)

The shared vocabulary for the STP Exception Triage domain. This is the source of
truth for naming in code, tests, API contracts, and UI copy. When a term here
changes, the code that uses it should change with it.

This glossary is owned by the architect (see CODEOWNERS) and updated as a diff
during the DDD phase via the `/ddd-update` skill. It is seeded from the existing
domain code (`src/domain/`) and `docs/architecture.md`.

## Core terms

| Term | Definition |
| --- | --- |
| **STP** | Straight-Through Processing — automated trade processing with no manual intervention. |
| **STP Exception** | A trade that failed straight-through processing and requires triage. Status: `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`. |
| **Triage** | The process of diagnosing and resolving an STP failure, combining deterministic rule checks and LangGraph agents. |
| **Triage Run** | One execution of triage for a trade, persisted with its steps, diagnosis, and root cause. |
| **Triage Step** | A single recorded action within a triage run (a tool call, decision, or agent step). |
| **FO** | Front Office — the trade-capture and validation stage. |
| **BO** | Back Office — the settlement-side validation stage. |
| **Rule Check** | A deterministic validation (FO or BO) that passes or fails without an LLM. Defined in `src/domain/check_rules.py`. |
| **Root Cause** | The classified reason a trade failed (see Root Cause codes). |
| **HITL** | Human-in-the-Loop — a write action that requires explicit human approval before it executes. |
| **Triage Resume** | Continuing a `PENDING_APPROVAL` triage run after the operator's decision: approve executes the pending HITL action, reject skips it; either way the run proceeds to a final diagnosis. |
| **Trade Event** | An `AMEND` or `CANCEL` event applied to a trade, creating a new trade version. |
| **SSI** | Settlement Standing Instruction — settlement details (BIC, account, IBAN) for a counterparty/currency pair. |
| **Counterparty** | The other party to a trade, identified by an LEI; may be active or inactive. |
| **LEI** | Legal Entity Identifier — the counterparty identifier. |
| **Counterparty Search** | Finding a counterparty during trade creation by **partial-name** or **partial-LEI** (substring, case-insensitive) match — reusing the existing `GET /api/v1/counterparties` filtering. The result set is the candidate counterparties an operator chooses from; selecting one binds its LEI (and name, for display) to the trade. |
| **Counterparty Selection** | The act of choosing one counterparty from a Counterparty Search result and writing it back to the trade form, displayed as `LEI + name`. |
| **Reference Data** | Instrument metadata (description, asset class, active flag). |
| **Value Date** | The settlement date of a trade; subject to business-day and validity rules. |
| **Settlement Tenor** | The span between a trade's trade date and its value date. |
| **Maximum Settlement Tenor** | The upper bound on settlement tenor that the FO check tolerates; a value date beyond it is flagged as a likely data-entry error (maps to the `INVALID_VALUE_DATE` root cause). |

## Trade workflow status

The `TradeWorkflowStatus` lifecycle (`src/domain/entities.py`). See the state
diagram in `docs/domain/model.md`.

| Status | Meaning |
| --- | --- |
| `Initial` | Trade created, not yet checked. |
| `FoCheck` | Running FO rule checks. |
| `FoAgentToCheck` | FO rules failed; FO agent is investigating. |
| `FoUserToValidate` | FO triage needs a human decision (HITL). |
| `FoValidated` | FO stage passed. |
| `BoCheck` | Running BO rule checks. |
| `BoAgentToCheck` | BO rules failed; BO agent is investigating. |
| `BoUserToValidate` | BO triage needs a human decision (HITL). |
| `BoValidated` | BO stage passed. |
| `Done` | Trade fully validated. |
| `Cancelled` | Trade cancelled via an approved cancel event. |
| `EventPending` | An amend/cancel event is pending and blocks manual triage. |

## Root cause codes

From `RootCause` (`src/domain/entities.py`).

| Code | Meaning |
| --- | --- |
| `MISSING_SSI` | No settlement instruction for the counterparty/currency. |
| `BIC_FORMAT_ERROR` | Malformed BIC. |
| `INVALID_VALUE_DATE` | Value date violates business-day/validity rules. |
| `INSTRUMENT_NOT_FOUND` | Instrument missing from reference data. |
| `COUNTERPARTY_NOT_FOUND` | Counterparty not found. |
| `SWIFT_AC01` | SWIFT AC01 — incorrect account number. |
| `SWIFT_AG01` | SWIFT AG01 — transaction forbidden / account closed (counterparty inactive). |
| `IBAN_FORMAT_ERROR` | Malformed IBAN. |
| `COMPOUND_FAILURE` | Multiple concurrent failures requiring the ReAct path. |
| `UNKNOWN` | Unclassified; handled by the autonomous investigation path. |

## Conventions

- New terms are added with a definition and, where relevant, a link to the
  enum or module that realizes them.
- If a feature needs a concept not listed here, the DDD phase adds it **before**
  the BDD phase writes scenarios that use it.
- Avoid synonyms: pick one term and use it everywhere (code, tests, UI).
