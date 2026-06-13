# Spec: FO value date validation

Data-model and rule specification for the Front Office value-date checks.
Vocabulary: `docs/domain/glossary.md`. Behavior: `features/fo_value_date_validation.feature`
(business) and `features/specs/fo_value_date.spec.feature` (detailed).

## Surface

| Aspect | Value |
| --- | --- |
| API contract | `POST /api/v1/trades/{trade_id}/fo-check` (see `docs/api/openapi.json`) |
| Domain rules | `src/domain/check_rules.py` (`FO_RULES`) |
| Root cause on failure | `INVALID_VALUE_DATE` (`src/domain/entities.py`) |

## Input fields

The rules read these fields of a trade (subset of `TradeDetail` in
`src/domain/entities.py`):

| Field | Type | Notes |
| --- | --- | --- |
| `trade_date` | `date` | When the trade was agreed. |
| `input_date` | `date` | When the trade was captured. |
| `value_date` | `date` | Settlement date — the subject of these rules. |

## Rules and constraints

| Rule name | Severity | Constraint | Fails when |
| --- | --- | --- | --- |
| `value_date_after_trade_date` | error | Value date must be strictly after the trade date. | `value_date <= trade_date` |
| `value_date_not_past` | error | Value date must not be before today. | `value_date < today` |
| `value_date_settlement_cycle` | warning | Value date should meet the T+2 FX settlement cycle. | `value_date < trade_date + 2 days` |

Notes:

- `value_date_settlement_cycle` is **warning** severity: it flags but does not by
  itself block, whereas `value_date_after_trade_date` and `value_date_not_past`
  are **error** severity.
- T+2 uses calendar days in the current implementation, not business days. A
  business-day calendar is a separate concern (see `_trade_date_not_weekend` and
  the calendar service).

## Boundary specification

The executable boundaries are in `features/specs/fo_value_date.spec.feature`:

| Rule | Input (trade date 2026-06-01) | Outcome |
| --- | --- | --- |
| after-trade-date | value date 2026-05-31 (before) | fail |
| after-trade-date | value date 2026-06-01 (on date) | fail |
| after-trade-date | value date 2026-06-02 (T+1) | pass |
| settlement-cycle | value date 2026-06-02 (T+1) | fail |
| settlement-cycle | value date 2026-06-03 (T+2) | pass |
| settlement-cycle | value date 2026-06-10 (>T+2) | pass |

## Change protocol

Changing any constraint above requires: update this spec and the
`spec.feature`, regenerate `docs/api/openapi.json` if the contract shape
changes (`uv run python scripts/export_openapi.py`), then implement under TDD.
