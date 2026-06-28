Feature: Counterparty search for trade creation
  An operator creating a trade needs to find a counterparty by name or LEI
  through a search modal instead of a long dropdown, so the right counterparty
  can be located quickly and written back to the trade form.

  Background:
    Given the counterparty master contains:
      | lei                  | name                  |
      | 213800QILIUD4ROSUO03 | Acme Bank Ltd         |
      | 5493001KJTIIGC8Y1R12 | Global Securities Inc |
      | 9695005MSX1OYEMGDF46 | Pacific Finance Corp  |

  Scenario Outline: A search term matches the name or the LEI, case-insensitively
    When the operator searches counterparties for "<term>"
    Then the results include the counterparty named "<name>"

    Examples:
      | term      | name                  |
      | acme      | Acme Bank Ltd         |
      | PACIFIC   | Pacific Finance Corp  |
      | secur     | Global Securities Inc |
      | 5493001   | Global Securities Inc |
      | iud4rosuo | Acme Bank Ltd         |
      | 9695005ms | Pacific Finance Corp  |

  Scenario: A search with no matching name or LEI returns nothing
    When the operator searches counterparties for "no-such-counterparty"
    Then no counterparties are returned

  Scenario: A selected result is identified by its LEI and name
    When the operator searches counterparties for "acme"
    And the operator selects the first result
    Then the selection shows LEI "213800QILIUD4ROSUO03" and name "Acme Bank Ltd"
