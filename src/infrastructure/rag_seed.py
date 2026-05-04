"""Seed initial static knowledge into the RAG vector store.

Includes SWIFT error code documentation and resolution pattern templates.
Run once after enabling pgvector on the Neon database:

    python -m src.infrastructure.rag_seed

Requires OPENAI_API_KEY and DATABASE_URL to be set.
"""

from __future__ import annotations

import logging

_logger = logging.getLogger("stp_triage.rag_seed")

# ---------------------------------------------------------------------------
# Static knowledge documents
# ---------------------------------------------------------------------------

_SWIFT_KNOWLEDGE: list[dict] = [
    {
        "source_type": "swift_knowledge",
        "source_id": "swift_ag01",
        "agent_type": None,
        "content": (
            "[SWIFT Code AG01] Counterparty Inactive / Not Authorized\n"
            "Meaning: The counterparty BIC is valid but the account or counterparty "
            "is not authorized to receive payments or is currently inactive.\n"
            "Typical causes: Counterparty suspended, account frozen, legal/compliance hold, "
            "merger/acquisition resulting in BIC change.\n"
            "BO Resolution: Reactivate the counterparty in the master data (reactivate_counterparty). "
            "Verify with counterparty directly that they are operational.\n"
            "FO Resolution: If FO receives AG01 sendback, confirm trade details are correct. "
            "The issue is on the BO/counterparty side."
        ),
        "metadata": {"swift_code": "AG01", "category": "counterparty"},
    },
    {
        "source_type": "swift_knowledge",
        "source_id": "swift_ac01",
        "agent_type": None,
        "content": (
            "[SWIFT Code AC01] Missing or Invalid SSI / Incorrect Account\n"
            "Meaning: The account number in the payment instruction is incorrect or does not exist "
            "at the receiving bank. Often indicates a missing or outdated Settlement Standing "
            "Instruction (SSI).\n"
            "Typical causes: SSI never registered, SSI has wrong account/IBAN, account closed "
            "or changed at counterparty bank.\n"
            "BO Resolution: Look up external SSI (lookup_external_ssi). If found, register it "
            "(register_ssi). If not found, escalate to BO user for manual SSI setup.\n"
            "FO Resolution: FO is not responsible for SSI data. AC01 is always a BO-side issue."
        ),
        "metadata": {"swift_code": "AC01", "category": "ssi"},
    },
    {
        "source_type": "swift_knowledge",
        "source_id": "swift_be01",
        "agent_type": None,
        "content": (
            "[SWIFT Code BE01] BIC / IBAN Format Error\n"
            "Meaning: The BIC (Bank Identifier Code) or IBAN (International Bank Account Number) "
            "in the settlement instruction does not match the expected format.\n"
            "Typical causes: Typo when SSI was entered, BIC changed due to bank restructuring, "
            "IBAN has wrong country code or check digits.\n"
            "BO Resolution: Cannot self-correct — the correct values must come from the counterparty. "
            "Escalate to BO user with details of which field is wrong and its current value. "
            "Once correct values are obtained, use update_ssi to fix the SSI.\n"
            "Validation: BIC format is 8 or 11 chars (4 bank + 2 country + 2 location + optional 3 branch). "
            "IBAN format is country-specific (e.g. GB: 22 chars, DE: 22 chars)."
        ),
        "metadata": {"swift_code": "BE01", "category": "format"},
    },
    {
        "source_type": "swift_knowledge",
        "source_id": "swift_am04",
        "agent_type": None,
        "content": (
            "[SWIFT Code AM04] Insufficient Funds / FO Liquidity Issue\n"
            "Meaning: The sending account does not have sufficient funds or credit limit to cover "
            "the payment. This is a Front-Office side issue related to trade economics.\n"
            "Typical causes: Position limit exceeded, wrong amount entered by FO, liquidity "
            "shortfall on trade date, wrong settlement currency.\n"
            "BO Resolution: This is a FO-side problem. Send back to FO (send_back_to_fo) if "
            "sendback_count is 0. If sendback_count >= 1 (already returned once), escalate to "
            "BO user — further sendback is prohibited.\n"
            "FO Resolution: Check trade amount, settlement currency, and value date. "
            "Amend if data error (create_amend_event), or cancel if fundamentally wrong "
            "(create_cancel_event)."
        ),
        "metadata": {"swift_code": "AM04", "category": "fo_side"},
    },
]

_RESOLUTION_TEMPLATES: list[dict] = [
    {
        "source_type": "resolution_template",
        "source_id": "tpl_missing_ssi_found",
        "agent_type": "bo",
        "content": (
            "[BO RESOLUTION TEMPLATE] Missing SSI — External SSI Found\n"
            "Triage path: MISSING_SSI\n"
            "Scenario: ssi_exists rule failed. External SSI lookup returned a valid record.\n"
            "Resolution steps:\n"
            "1. Call lookup_external_ssi(lei, currency) to retrieve SSI details\n"
            "2. Call register_ssi(lei, currency, bic, account, iban) with those values (HITL approval required)\n"
            "3. After approval, trade can proceed to settlement\n"
            "Root cause: MISSING_SSI\n"
            "Outcome: COMPLETED after operator approves register_ssi"
        ),
        "metadata": {"triage_path": "MISSING_SSI", "outcome": "register_ssi"},
    },
    {
        "source_type": "resolution_template",
        "source_id": "tpl_missing_ssi_not_found",
        "agent_type": "bo",
        "content": (
            "[BO RESOLUTION TEMPLATE] Missing SSI — No External SSI Found\n"
            "Triage path: MISSING_SSI\n"
            "Scenario: ssi_exists rule failed. External SSI lookup returned no results.\n"
            "Resolution steps:\n"
            "1. Call lookup_external_ssi(lei, currency) — returns found=false\n"
            "2. Call escalate_to_bo_user explaining no SSI exists internally or externally\n"
            "3. BO user must manually contact counterparty to obtain SSI details\n"
            "Root cause: MISSING_SSI\n"
            "Outcome: Escalated to BO user for manual SSI setup"
        ),
        "metadata": {"triage_path": "MISSING_SSI", "outcome": "escalate"},
    },
    {
        "source_type": "resolution_template",
        "source_id": "tpl_fo_value_date_error",
        "agent_type": "fo",
        "content": (
            "[FO RESOLUTION TEMPLATE] Invalid Value Date\n"
            "Triage path: FO_ERROR\n"
            "Scenario: trade_date_valid or value_date_valid rule failed. Value date is in the past "
            "or before trade date.\n"
            "Resolution steps:\n"
            "1. Call get_trade_detail to confirm current dates\n"
            "2. If value_date is clearly wrong (e.g. typo or past date): "
            "call create_amend_event with amended_fields={\"value_date\": \"YYYY-MM-DD\"}\n"
            "3. Operator approves amendment, trade gets new version with corrected date\n"
            "Root cause: INVALID_VALUE_DATE\n"
            "Outcome: COMPLETED after operator approves create_amend_event"
        ),
        "metadata": {"triage_path": "FO_ERROR", "root_cause": "INVALID_VALUE_DATE"},
    },
    {
        "source_type": "resolution_template",
        "source_id": "tpl_compound_failure",
        "agent_type": "bo",
        "content": (
            "[BO RESOLUTION TEMPLATE] Compound Failure — Multiple Issues\n"
            "Triage path: COMPOUND\n"
            "Scenario: Multiple BoCheck rules failed simultaneously (e.g. both counterparty_active "
            "and ssi_exists failed, or bic_format_valid and ssi_exists).\n"
            "Resolution approach: Address each issue independently in order of severity:\n"
            "1. Counterparty inactive + missing SSI: First reactivate counterparty (AG01), "
            "then handle SSI (AC01)\n"
            "2. Format errors (BE01) + missing SSI: Escalate BE01 to BO user, "
            "simultaneously look up and register new SSI\n"
            "3. FO-side issues mixed with BO-side: Send back to FO for FO-side items first\n"
            "Root cause: COMPOUND_FAILURE\n"
            "Use deep investigation mode to reason through each component"
        ),
        "metadata": {"triage_path": "COMPOUND", "root_cause": "COMPOUND_FAILURE"},
    },
]


def seed_static_knowledge() -> int:
    """Embed and store static SWIFT knowledge and resolution templates.

    Returns the number of chunks stored. Skips chunks that already exist
    (by source_id). Safe to call multiple times.
    """
    from src.infrastructure.rag_service import _rag_service

    all_docs = _SWIFT_KNOWLEDGE + _RESOLUTION_TEMPLATES
    stored = 0
    for doc in all_docs:
        _rag_service.store_chunk(
            content=doc["content"],
            source_type=doc["source_type"],
            source_id=doc.get("source_id"),
            agent_type=doc.get("agent_type"),
            metadata=doc.get("metadata"),
        )
        stored += 1
        _logger.info("rag_seed: stored %s", doc.get("source_id"))

    return stored


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO)
    n = seed_static_knowledge()
    print(f"Seeded {n} RAG chunks.")
