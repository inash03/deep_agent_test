Feature: BO triage HITL resume — detailed specification (SDD)
  Refines features/bo_triage_hitl.feature for the AG01 (counterparty inactive)
  deterministic path. Starting BO triage pauses at the reactivate-counterparty
  HITL node (status PENDING_APPROVAL). Resuming with approved=true executes the
  reactivation and completes with action_taken=true; approved=false skips the
  action (the tool is never called) and completes with action_taken=false.
  Contract: POST /api/v1/trades/{trade_id}/bo-triage/{run_id}/resume.

  Background:
    Given a BO triage run paused at the reactivate-counterparty approval

  Scenario: Starting triage pauses for approval
    Then the pending action type is "reactivate_counterparty"
    And the triage status is "PENDING_APPROVAL"

  Scenario Outline: resume executes or skips the action
    When the operator resumes with approved "<approved>"
    Then the triage status is "COMPLETED"
    And action_taken is "<action_taken>"
    And the reactivate tool was called <calls> times

    Examples:
      | approved | action_taken | calls |
      | true     | true         | 1     |
      | false    | false        | 0     |
