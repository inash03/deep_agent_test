# Spec: Counterparty search

Data-model and contract specification for the counterparty master search that
backs the trade-creation search modal (Issue #61). Vocabulary:
`docs/domain/glossary.md` (Counterparty, LEI). Behavior:
`features/counterparty_search.feature` (business) and
`features/specs/counterparty_search.spec.feature` (detailed).

## Surface

| Aspect | Value |
| --- | --- |
| API contract | `GET /api/v1/counterparties` — **unchanged** (the `lei` and `name` partial-match query params already exist; `docs/api/openapi.json` is not modified) |
| BFF path | browser → `/api/backend/counterparties` → `/api/v1/counterparties` (the browser never calls Cloud Run directly — see `docs/architecture.md`) |
| Router | `src/presentation/routers/counterparties.py` (`list_counterparties`) |
| Filtering | `src/infrastructure/db/counterparty_repository.py` (`CounterpartyRepository.list`) |
| Table | `counterparties` (`src/infrastructure/db/models.py`, `CounterpartyModel`) |

The search modal reuses the existing list endpoint; no new endpoint, schema, or
field is added, so `tests/unit/test_openapi_contract.py` stays green.

## Query parameters

| Param | Type | Default | Constraint | Meaning |
| --- | --- | --- | --- | --- |
| `name` | string \| null | `null` | — | Substring filter on counterparty name. |
| `lei` | string \| null | `null` | — | Substring filter on LEI. |
| `limit` | int | `20` | `1 <= limit <= 100` | Page size. |
| `offset` | int | `0` | `offset >= 0` | Page start. |

## Matching semantics

| Aspect | Rule |
| --- | --- |
| Match type | **Substring** — matches any part of the value, not only the prefix. Implemented as `column ILIKE '%' || term || '%'`. |
| Case | **Case-insensitive** in both directions (upper-case term matches lower-case data and vice versa), via `ILIKE`. |
| Fields | Applied independently to `name` and to `lei`. |
| Combination | `name` and `lei` filters **AND** together; a row must satisfy every supplied filter. |
| Empty / absent term | A `null`, empty, or whitespace-only term applies **no** filter for that field (current `if name:` / `if lei:` behavior); supplying neither returns the whole master, paginated. |
| Ordering | Results are ordered by `name` **ascending**. |
| `total` | Counts **all** matching rows, independent of `limit`/`offset`; `items` is the page. |

> Issue #61 says "name-prefix and partial-LEI search". This spec **supersedes**
> that wording: both `name` and `lei` use substring, case-insensitive matching.
> The repository already implements this (`.ilike(f"%{term}%")`), so no code
> change is required for the matching rule itself — this spec locks it.

## Response

`CounterpartyListResponse` = `{ items: CounterpartyOut[], total: int }`, where
`CounterpartyOut` = `{ lei, name, bic, is_active }`. The modal identifies a
selected counterparty by its `lei` + `name` and writes that back to the trade
form (see `features/counterparty_search.feature`).

## Error mapping

| Condition | Outcome |
| --- | --- |
| No rows match the filters | HTTP **200** with `items: []`, `total: 0` (an empty result is not an error — there is no 404 on the list endpoint). |
| `limit` outside `1..100`, or `offset < 0`, or non-integer | HTTP **422** (FastAPI query validation, `HTTPValidationError`). |

## Data model

No migration. The search reads the existing `counterparties` table and persists
no new state:

| Column | Type | Notes |
| --- | --- | --- |
| `lei` | `String(30)` PK | Searched (substring, case-insensitive). |
| `name` | `String(200)` | Searched (substring, case-insensitive); sort key. |
| `bic` | `String(15)` | Returned, not searched. |
| `is_active` | `Boolean` | Returned, not searched (the modal does not filter on active for this feature). |

## Known characteristics (out of scope)

- The term is interpolated into an `ILIKE` pattern, so SQL `LIKE` wildcards
  (`%`, `_`) in a term are interpreted as wildcards rather than literals. This
  matches the existing endpoint behavior and is not changed here; escaping is
  out of scope for Issue #61.
- No relevance ranking — ordering is purely alphabetical by name.

## Change protocol

Changing the matching semantics, query params, or response shape requires:
update this spec and `features/specs/counterparty_search.spec.feature`,
regenerate `docs/api/openapi.json` if the contract shape changes
(`uv run python scripts/export_openapi.py`), then implement under TDD. The
substring + case-insensitive behavior on both fields must remain covered.
