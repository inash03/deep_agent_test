Feature: FO maximum settlement tenor — detailed specification (SDD)
  Refines features/fo_max_tenor.feature down to the implementable boundary.
  The maximum settlement tenor is 730 days (MAX_SETTLEMENT_TENOR_DAYS). A value
  date more than 730 days after the trade date fails the rule (severity:
  warning) and maps to the INVALID_VALUE_DATE root cause. The rule checks only
  the upper bound; the lower bound is owned by the other value-date rules.

  Scenario Outline: maximum settlement tenor boundary
    Given a trade with trade date "2026-06-01"
    And a value date <days> days after the trade date
    When the maximum settlement tenor check runs
    Then the rule result is "<outcome>"

    Examples:
      | days | outcome | note                                       |
      | 0    | pass    | same day; lower bound is another rule      |
      | 730  | pass    | exactly the maximum tenor (the boundary)   |
      | 731  | fail    | one day beyond the maximum                 |
      | 4000 | fail    | far beyond the maximum                     |
