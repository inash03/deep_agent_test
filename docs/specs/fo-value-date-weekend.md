# Spec: FO value date weekend validation

Data-model and rule specification for the Front Office value-date **weekend**
check. Vocabulary: `docs/domain/glossary.md`. Behavior:
`features/fo_value_date_weekend.feature` (business) and
`features/specs/fo_value_date_weekend.spec.feature` (detailed).

Sister rule to `_trade_date_not_weekend`; complements the value-date rules in
`docs/specs/fo-value-date.md`.

## Surface

| Aspect | Value |
| --- | --- |
| API contract | `POST /api/v1/trades/{trade_id}/fo-check` — **unchanged** (no new endpoint, schema, or field; `docs/api/openapi.json` is not modified) |
| Domain rules | `src/domain/check_rules.py` (`FO_RULES`) |
| Root cause on failure | `INVALID_VALUE_DATE` (`src/domain/entities.py`) |

The rule surfaces through the existing FO-check flow: a failing **error**-severity
rule moves the trade `FoCheck → FoAgentToCheck` exactly like the other FO error
rules. No contract change is required, so `tests/unit/test_openapi_contract.py`
stays green.

## Input fields

Subset of `TradeModel` already read by the FO rules:

| Field | Type | Notes |
| --- | --- | --- |
| `value_date` | `date` | Settlement date — the subject of this rule. |

## Rule and constraint

| Rule name | Severity | Constraint | Fails when |
| --- | --- | --- | --- |
| `value_date_not_weekend` | error | Value date must fall on a business day (Mon–Fri). | `value_date.weekday() >= 5` (Saturday or Sunday) |

Notes:

- Severity is **error** (consistent with `trade_date_not_weekend`): a weekend
  value date blocks straight-through processing and routes to FO triage.
- Weekend only. Public-holiday calendars are a separate concern (no holiday
  calendar service exists yet); this rule intentionally checks Sat/Sun only,
  matching `_trade_date_not_weekend`.
- Failure message names the offending day (`Saturday`/`Sunday`), mirroring the
  trade-date rule, so triage and the FO agent get a human-readable reason.
- No new migration: the rule reads an existing column and adds no persisted
  state.

## Boundary specification

Executable boundaries in `features/specs/fo_value_date_weekend.spec.feature`
(trade date 2026-06-01, a Monday):

| Input value date | Weekday | Outcome |
| --- | --- | --- |
| 2026-06-05 | Friday | pass |
| 2026-06-06 | Saturday | fail |
| 2026-06-07 | Sunday | fail |
| 2026-06-08 | Monday | pass |
</content>
