Feature: FO value date validation — detailed specification (SDD)
  Refines features/fo_value_date_validation.feature down to the implementable
  boundary and error cases. These are the SDD detailed scenarios and are the
  direct input to the TDD phase. A failing value-date rule maps to the
  INVALID_VALUE_DATE root cause (see docs/domain/glossary.md).

  Scenario Outline: value-date-after-trade-date boundary
    Given a trade with trade date "2026-06-01"
    And a value date of "<value_date>"
    When the value-date-after-trade-date rule runs
    Then the rule result is "<outcome>"

    Examples:
      | value_date | outcome | note                  |
      | 2026-05-31 | fail    | before the trade date |
      | 2026-06-01 | fail    | on the trade date     |
      | 2026-06-02 | pass    | one day after         |

  Scenario Outline: settlement-cycle T+2 boundary
    Given a trade with trade date "2026-06-01"
    And a value date of "<value_date>"
    When the settlement cycle rule runs
    Then the rule result is "<outcome>"

    Examples:
      | value_date | outcome | note                       |
      | 2026-06-02 | fail    | T+1, earlier than T+2      |
      | 2026-06-03 | pass    | exactly T+2 (the boundary) |
      | 2026-06-10 | pass    | well beyond T+2            |
