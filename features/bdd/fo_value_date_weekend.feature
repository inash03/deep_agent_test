Feature: Front Office value date weekend validation
  Operations needs trades whose value date falls on a weekend to fail the Front
  Office rule check, so a settlement is never scheduled on a non-business day and
  the trade is triaged instead.

  Scenario: A value date on a Saturday is rejected
    Given a trade with trade date "2026-06-01"
    And a value date of "2026-06-06"
    When the value-date-not-weekend rule runs
    Then the rule fails
    And the failure message mentions "Saturday"

  Scenario: A value date on a Sunday is rejected
    Given a trade with trade date "2026-06-01"
    And a value date of "2026-06-07"
    When the value-date-not-weekend rule runs
    Then the rule fails
    And the failure message mentions "Sunday"

  Scenario: A value date on a weekday passes
    Given a trade with trade date "2026-06-01"
    And a value date of "2026-06-05"
    When the value-date-not-weekend rule runs
    Then the rule passes
