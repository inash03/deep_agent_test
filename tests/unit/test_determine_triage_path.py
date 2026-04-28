"""Unit tests for _determine_triage_path() — no DB, no LLM required."""

import pytest

from src.infrastructure.bo_agent import _determine_triage_path


# ---------------------------------------------------------------------------
# Parametrized test cases
# (error_message, failed_rules, expected_triage_path)
# ---------------------------------------------------------------------------

CASES = [
    # --- AG01 (counterparty inactive) ---
    ("MT103 rejected by SWIFT. Reason code: AG01.", [], "AG01"),
    ("AG01 counterparty inactive", [], "AG01"),
    # rule-name detection (no SWIFT code in message)
    ("Pre-settlement check failed.", ["counterparty_active"], "AG01"),

    # --- BE01 (BIC / IBAN format error) ---
    ("BE01 BIC mismatch detected.", [], "BE01"),
    ("Custodian rejected. BE01.", [], "BE01"),
    # rule-name detection
    ("Settlement instruction invalid.", ["bic_format_valid"], "BE01"),
    ("Settlement instruction invalid.", ["iban_format_valid"], "BE01"),

    # --- AM04 (FO-side liquidity) ---
    ("MT103 rejected by SWIFT. Reason code: AM04.", [], "AM04"),
    ("AM04 insufficient funds.", [], "AM04"),

    # --- MISSING_SSI (AC01 or ssi_exists rule) ---
    ("MT103 rejected by SWIFT. Reason code: AC01.", [], "MISSING_SSI"),
    ("AC01 account closed.", [], "MISSING_SSI"),
    # rule-name detection
    ("Pre-settlement: ssi_exists failed.", ["ssi_exists"], "MISSING_SSI"),

    # --- COMPOUND (multiple conditions match) ---
    # Two SWIFT codes in the same message
    ("AG01 BE01 both detected.", [], "COMPOUND"),
    # Two rule failures
    ("Multiple checks failed.", ["counterparty_active", "ssi_exists"], "COMPOUND"),
    # SWIFT code + rule name
    ("AG01 detected.", ["ssi_exists"], "COMPOUND"),
    ("AM04 liquidity error.", ["bic_format_valid"], "COMPOUND"),

    # --- UNKNOWN (nothing matches) ---
    ("Generic settlement failure.", [], "UNKNOWN"),
    ("Settlement SLA breach. No further details.", [], "UNKNOWN"),
    ("", [], "UNKNOWN"),
    ("Generic error.", ["counterparty_exists"], "UNKNOWN"),  # unrecognised rule
]


@pytest.mark.parametrize("error_message,failed_rules,expected", CASES)
def test_determine_triage_path(error_message: str, failed_rules: list, expected: str) -> None:
    result = _determine_triage_path(error_message, failed_rules)
    assert result == expected, (
        f"error_message={error_message!r}, failed_rules={failed_rules} → "
        f"got {result!r}, expected {expected!r}"
    )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_case_insensitive_swift_codes() -> None:
    """SWIFT codes must be detected regardless of original message casing."""
    assert _determine_triage_path("reason code: ag01.", []) == "AG01"
    assert _determine_triage_path("Reason Code: Be01", []) == "BE01"
    assert _determine_triage_path("am04 LIQUIDITY", []) == "AM04"
    assert _determine_triage_path("ac01 ACCOUNT", []) == "MISSING_SSI"


def test_empty_failed_rules_with_no_swift_is_unknown() -> None:
    assert _determine_triage_path("Unknown settlement error", []) == "UNKNOWN"


def test_single_unrecognised_rule_is_unknown() -> None:
    assert _determine_triage_path("", ["risk_limit_breach"]) == "UNKNOWN"
    assert _determine_triage_path("", ["counterparty_exists"]) == "UNKNOWN"


def test_compound_three_conditions() -> None:
    """Three independently matching conditions → still COMPOUND."""
    result = _determine_triage_path(
        "AG01 BE01 AM04 all present.",
        ["counterparty_active", "bic_format_valid"],
    )
    assert result == "COMPOUND"
