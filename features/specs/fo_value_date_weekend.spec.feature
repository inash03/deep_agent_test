Feature: FO value date weekend validation — detailed specification (SDD)
  Refines features/fo_value_date_weekend.feature down to the implementable
  weekday boundary. These are the SDD detailed scenarios and the direct input to
  the TDD phase. A failing rule is error severity and maps to the
  INVALID_VALUE_DATE root cause (see docs/domain/glossary.md).

  Scenario Outline: value-date-not-weekend weekday boundary
    Given a trade with trade date "2026-06-01"
    And a value date of "<value_date>"
    When the value-date-not-weekend rule runs
    Then the rule result is "<outcome>"

    Examples:
      | value_date | outcome | note               |
      | 2026-06-05 | pass    | Friday (business)  |
      | 2026-06-06 | fail    | Saturday           |
      | 2026-06-07 | fail    | Sunday             |
      | 2026-06-08 | pass    | Monday (business)  |

  Scenario: the failure message names the offending weekend day
    Given a trade with trade date "2026-06-01"
    And a value date of "2026-06-06"
    When the value-date-not-weekend rule runs
    Then the rule fails
    And the failure message mentions "Saturday"
