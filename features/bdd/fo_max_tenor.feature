Feature: Front Office maximum settlement tenor check
  Operations needs trades whose value date is implausibly far in the future to
  be flagged during the Front Office check, so likely data-entry errors in the
  settlement date are caught for review before processing.

  Scenario: A value date within the maximum settlement tenor is accepted
    Given a trade with trade date "2026-06-01"
    And a value date 30 days after the trade date
    When the maximum settlement tenor check runs
    Then the trade passes the check

  Scenario: A value date beyond the maximum settlement tenor is flagged for review
    Given a trade with trade date "2026-06-01"
    And a value date 4000 days after the trade date
    When the maximum settlement tenor check runs
    Then the trade is flagged for review
