Feature: Front Office value date validation
  Operations needs trades with an invalid value date to fail the Front Office
  rule check, so settlement problems are caught before straight-through
  processing rather than after.

  Scenario: A value date on the trade date is rejected
    Given a trade with trade date "2026-06-01"
    And a value date of "2026-06-01"
    When the value-date-after-trade-date rule runs
    Then the rule fails
    And the failure message mentions "must be strictly after"

  Scenario: A value date earlier than T+2 fails the settlement cycle rule
    Given a trade with trade date "2026-06-01"
    And a value date of "2026-06-02"
    When the settlement cycle rule runs
    Then the rule fails
    And the failure message mentions "T+2"

  Scenario: A value date at T+2 passes the settlement cycle rule
    Given a trade with trade date "2026-06-01"
    And a value date of "2026-06-03"
    When the settlement cycle rule runs
    Then the rule passes
