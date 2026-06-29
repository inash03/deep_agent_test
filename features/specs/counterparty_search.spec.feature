Feature: Counterparty search — detailed specification (SDD)
  Refines features/counterparty_search.feature down to the implementable
  boundary, edge, and combination cases for the counterparty master search that
  backs the trade-creation search modal. These SDD detailed scenarios are the
  direct input to the TDD phase.

  The search is exposed by GET /api/v1/counterparties (lei / name query params)
  and implemented by CounterpartyRepository.list. Matching is by SUBSTRING
  (matches any part of the value, not only the prefix) and is CASE-INSENSITIVE,
  for both name and LEI. This supersedes the "prefix" wording in Issue #61.

  Background:
    Given the counterparty master contains:
      | lei                  | name                  |
      | 213800QILIUD4ROSUO03 | Acme Bank Ltd         |
      | 5493001KJTIIGC8Y1R12 | Global Securities Inc |
      | 9695005MSX1OYEMGDF46 | Pacific Bank Corp     |

  # --- Name: substring + case-insensitive ---------------------------------
  Scenario Outline: name search matches any substring, ignoring case
    When the operator searches counterparties by name "<term>"
    Then the search result names in order are "<names>"

    Examples:
      | term | names                             | note                         |
      | acme | Acme Bank Ltd                     | lowercase term, mixed data   |
      | ACME | Acme Bank Ltd                     | uppercase term, mixed data   |
      | bank | Acme Bank Ltd,Pacific Bank Corp   | substring in the middle      |
      | BANK | Acme Bank Ltd,Pacific Bank Corp   | middle substring, upper term |
      | ltd  | Acme Bank Ltd                     | substring at the end         |
      | zzz  |                                   | no match                     |

  # --- LEI: substring + case-insensitive ----------------------------------
  Scenario Outline: LEI search matches any substring, ignoring case
    When the operator searches counterparties by LEI "<term>"
    Then the search result names in order are "<names>"

    Examples:
      | term   | names                 | note                           |
      | 213800 | Acme Bank Ltd         | prefix of the LEI              |
      | qiliud | Acme Bank Ltd         | middle substring, lower term   |
      | QILIUD | Acme Bank Ltd         | middle substring, upper term   |
      | gdf46  | Pacific Bank Corp     | suffix of the LEI, lower term  |
      | 0000   |                       | no match                       |

  # --- Combining filters ---------------------------------------------------
  Scenario: name and LEI filters combine with AND
    When the operator searches counterparties by name "bank" and LEI "213800"
    Then the search result names in order are "Acme Bank Ltd"

  Scenario: combined filters that no single row satisfies return nothing
    When the operator searches counterparties by name "bank" and LEI "5493"
    Then the search returns no counterparties

  # --- Empty term ----------------------------------------------------------
  Scenario: a blank name term applies no filter and returns the whole master
    When the operator searches counterparties by name ""
    Then the search result names in order are "Acme Bank Ltd,Global Securities Inc,Pacific Bank Corp"

  # --- Ordering ------------------------------------------------------------
  Scenario: results are ordered by name ascending
    When the operator searches counterparties by name "bank"
    Then the search result names in order are "Acme Bank Ltd,Pacific Bank Corp"

  # --- Pagination ----------------------------------------------------------
  Scenario: the page is capped by the limit while the total counts all matches
    When the operator searches counterparties by name "bank" with limit 1
    Then the search result names in order are "Acme Bank Ltd"
    And the total match count is 2
