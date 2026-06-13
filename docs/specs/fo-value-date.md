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
| `value_date_within_max_tenor` | warning | Value date must not exceed the maximum settlement tenor. | `value_date > trade_date + MAX_SETTLEMENT_TENOR_DAYS` |

Notes:

- `value_date_settlement_cycle` and `value_date_within_max_tenor` are **warning**
  severity: they flag but do not by themselves block, whereas
  `value_date_after_trade_date` and `value_date_not_past` are **error** severity.
- T+2 uses calendar days in the current implementation, not business days. A
  business-day calendar is a separate concern (see `_trade_date_not_weekend` and
  the calendar service).
- **`MAX_SETTLEMENT_TENOR_DAYS = 730`** (about two years), defined in
  `src/domain/check_rules.py`. `value_date_within_max_tenor` checks only the
  **upper** bound; the lower bound (after trade date, T+2) is owned by the other
  rules. It is a sanity bound for likely data-entry errors, not a hard limit on
  legitimate long-dated forwards — hence warning severity.

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
| max-tenor | value date = trade date + 0 days | pass |
| max-tenor | value date = trade date + 730 days (the maximum) | pass |
| max-tenor | value date = trade date + 731 days | fail |
| max-tenor | value date = trade date + 4000 days | fail |

Detailed max-tenor boundaries are executed in
`features/specs/fo_max_tenor.spec.feature`.

## Change protocol

Changing any constraint above requires: update this spec and the
`spec.feature`, regenerate `docs/api/openapi.json` if the contract shape
changes (`uv run python scripts/export_openapi.py`), then implement under TDD.
