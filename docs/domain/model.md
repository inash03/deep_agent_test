# Domain Model

The structure of the STP Exception Triage domain. Terms used here are defined in
`docs/domain/glossary.md`. This model is seeded from `src/domain/entities.py`
and `docs/architecture.md`, and is updated during the DDD phase.

## Entity relationships

```mermaid
classDiagram
    class Trade {
        +string trade_id
        +string counterparty_lei
        +string instrument_id
        +string currency
        +Decimal amount
        +date value_date
        +TradeWorkflowStatus status
    }
    class TradeEvent {
        +EventType type
        +EventWorkflowStatus status
    }
    class Counterparty {
        +string lei
        +string name
        +bool is_active
    }
    class SettlementInstruction {
        +string lei
        +string currency
        +string bic
        +string account
        +string iban
    }
    class ReferenceData {
        +string instrument_id
        +string asset_class
        +bool is_active
    }
    class StpException {
        +StpExceptionStatus status
    }
    class TriageRun {
        +TriageStatus status
        +RootCause root_cause
    }
    class TriageStep

    Trade "1" --> "0..*" TradeEvent : amended/cancelled by
    Trade "*" --> "1" Counterparty : with
    Trade "*" --> "1" ReferenceData : references instrument
    Counterparty "1" --> "0..*" SettlementInstruction : has
    Trade "1" --> "0..*" StpException : may raise
    StpException "1" --> "0..*" TriageRun : resolved by
    TriageRun "1" --> "1..*" TriageStep : records
    TriageRun "*" --> "1" Trade : triages
```

## Trade workflow lifecycle

Mirrors `TradeWorkflowStatus` and the FO/BO triage flow in
`docs/architecture.md`.

```mermaid
stateDiagram-v2
    [*] --> Initial
    Initial --> FoCheck
    FoCheck --> FoValidated: all FO rules pass
    FoCheck --> FoAgentToCheck: FO rules fail
    FoAgentToCheck --> FoValidated: agent resolves
    FoAgentToCheck --> FoUserToValidate: HITL decision needed
    FoUserToValidate --> FoValidated: approved
    FoValidated --> BoCheck
    BoCheck --> Done: all BO rules pass
    BoCheck --> BoAgentToCheck: BO rules fail
    BoAgentToCheck --> Done: agent resolves
    BoAgentToCheck --> FoAgentToCheck: send back to FO
    BoAgentToCheck --> BoUserToValidate: HITL decision needed
    BoUserToValidate --> Done: approved
    Done --> Cancelled: cancel event approved
```

## Aggregates and invariants

- **Trade** is the central aggregate. Its `TradeWorkflowStatus` is the
  authoritative lifecycle state; transitions happen only through rule checks,
  agent resolution, or approved HITL actions.
- A **write action that changes operational data is always HITL** (register SSI,
  reactivate counterparty, send back to FO, apply event). Agents propose; humans
  approve.
- While a trade is `EventPending`, manual FO/BO triage is blocked.
- **TriageRun** records every step for auditability; it never mutates a trade
  directly — it produces proposals and records outcomes.

## Notes for agents

- Treat the enums in `src/domain/entities.py` as canonical. If a feature needs a
  new status or root cause, update this model and the glossary in the DDD phase
  first, then the enum, then tests, then code.
- Keep the domain layer framework-light (no FastAPI, no SQLAlchemy in
  `src/domain/`), per `CLAUDE.md`.
