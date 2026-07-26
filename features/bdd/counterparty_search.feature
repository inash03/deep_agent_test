Feature: Counterparty search for trade creation
  An operator creating a trade needs to find the other party quickly. Instead of
  scrolling a long dropdown, the operator searches the counterparty master by
  name or by LEI and picks one result, which is then identified on the form by
  its LEI and name. Search matches any part of the name or LEI and ignores
  letter case, so a remembered fragment is enough to find the counterparty.

  Background:
    Given the counterparty master contains:
      | lei                  | name                  |
      | 213800QILIUD4ROSUO03 | Acme Bank Ltd         |
      | 5493001KJTIIGC8Y1R12 | Global Securities Inc |
      | 9695005MSX1OYEMGDF46 | Pacific Bank Corp     |

  Scenario: Find a counterparty by part of its name, ignoring case
    When the operator searches counterparties by name "acme"
    Then the search results are:
      | name          |
      | Acme Bank Ltd |

  Scenario: A name fragment matches anywhere in the name, not only the start
    When the operator searches counterparties by name "bank"
    Then the search results are:
      | name              |
      | Acme Bank Ltd     |
      | Pacific Bank Corp |

  Scenario: Find a counterparty by part of its LEI, ignoring case
    When the operator searches counterparties by LEI "qiliud"
    Then the search results are:
      | name          |
      | Acme Bank Ltd |

  Scenario: A search that matches nothing returns no counterparties
    When the operator searches counterparties by name "Nonexistent"
    Then the search returns no counterparties

  Scenario: Selecting a result identifies the counterparty by LEI and name
    When the operator searches counterparties by name "acme"
    And the operator selects the only result
    Then the selected counterparty has LEI "213800QILIUD4ROSUO03" and name "Acme Bank Ltd"
