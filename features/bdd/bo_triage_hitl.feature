Feature: Back Office triage human-in-the-loop approval
  When BO triage proposes a write action (such as reactivating a counterparty),
  it pauses and waits for an operator decision. Operations needs approval to
  execute the action and rejection to skip it, so that no operational data is
  changed without explicit human consent — and either way the triage run
  finishes with a diagnosis.

  Scenario: The operator approves the pending action
    Given a BO triage run paused awaiting approval to reactivate a counterparty
    When the operator approves the pending action
    Then the triage run completes
    And the reactivation is executed
    And the action is recorded as taken

  Scenario: The operator rejects the pending action
    Given a BO triage run paused awaiting approval to reactivate a counterparty
    When the operator rejects the pending action
    Then the triage run completes
    And the reactivation is not executed
    And the action is recorded as not taken
