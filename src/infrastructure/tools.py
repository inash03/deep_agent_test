"""LangGraph tools for the STP Exception Triage Agent.

Data source selection:
  - If DATABASE_URL is set → reads from PostgreSQL via repositories (production)
  - Otherwise            → reads from in-memory mock_store (unit tests / dev without DB)

Eleven tools in two categories:
  Read-only (no side effects):
    - get_trade_detail
    - get_settlement_instructions
    - get_reference_data
    - get_counterparty
    - lookup_external_ssi
    - get_triage_history
    - get_counterparty_exception_history

  Write (side effects — requires HITL approval before calling):
    - register_ssi
    - reactivate_counterparty
    - update_ssi
    - escalate
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Generator

from langchain_core.tools import tool

from src.domain.entities import SettlementInstruction
from src.infrastructure import mock_store


# ---------------------------------------------------------------------------
# Data source context manager
# ---------------------------------------------------------------------------

@contextmanager
def _db_session() -> Generator:
    """Yields a DB session if DATABASE_URL is configured, else yields None."""
    if not os.environ.get("DATABASE_URL"):
        yield None
        return
    from src.infrastructure.db.session import make_session
    db = make_session()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Read-only tools
# ---------------------------------------------------------------------------


@tool
def get_trade_detail(trade_id: str) -> str:
    """Retrieve trade details from the trade system by trade ID.

    Returns trade information including counterparty LEI, instrument ID,
    currency, amount, value date, and settlement currency.
    Returns an error message if the trade is not found.
    """
    with _db_session() as db:
        if db is not None:
            from src.infrastructure.db.trade_repository import TradeRepository
            row = TradeRepository(db).get_by_trade_id(trade_id)
            if row is None:
                return json.dumps({"error": f"Trade '{trade_id}' not found in trade system."})
            return json.dumps({
                "trade_id": row.trade_id,
                "counterparty_lei": row.counterparty_lei,
                "instrument_id": row.instrument_id,
                "currency": row.currency,
                "amount": str(row.amount),
                "value_date": row.value_date.isoformat(),
                "settlement_currency": row.settlement_currency,
            })

    # Fallback: mock_store
    trade = mock_store.get_trade(trade_id)
    if trade is None:
        return json.dumps({"error": f"Trade '{trade_id}' not found in trade system."})
    return json.dumps({
        "trade_id": trade.trade_id,
        "counterparty_lei": trade.counterparty_lei,
        "instrument_id": trade.instrument_id,
        "currency": trade.currency,
        "amount": str(trade.amount),
        "value_date": trade.value_date.isoformat(),
        "settlement_currency": trade.settlement_currency,
    })


@tool
def get_settlement_instructions(lei: str, currency: str) -> str:
    """Look up the registered SSI (Settlement Standing Instructions) for a
    counterparty LEI and settlement currency in the internal SSI database.

    Returns SSI details (BIC, account, IBAN) if found.
    Returns not_found if no SSI is registered for this counterparty/currency pair.
    """
    with _db_session() as db:
        if db is not None:
            from src.infrastructure.db.ssi_repository import SsiRepository
            row = SsiRepository(db).get(lei, currency, is_external=False)
            if row is None:
                return json.dumps({
                    "found": False, "lei": lei, "currency": currency,
                    "message": f"No SSI registered for LEI '{lei}' / currency '{currency}'.",
                })
            return json.dumps({
                "found": True, "lei": row.lei, "currency": row.currency,
                "bic": row.bic, "account": row.account, "iban": row.iban,
            })

    ssi = mock_store.get_ssi(lei, currency)
    if ssi is None:
        return json.dumps({
            "found": False, "lei": lei, "currency": currency,
            "message": f"No SSI registered for LEI '{lei}' / currency '{currency}'.",
        })
    return json.dumps({
        "found": True, "lei": ssi.lei, "currency": ssi.currency,
        "bic": ssi.bic, "account": ssi.account, "iban": ssi.iban,
    })


@tool
def get_reference_data(instrument_id: str) -> str:
    """Look up instrument reference data by instrument ID.

    Returns description, asset class, and active status.
    Returns an error message if the instrument is not found.
    """
    with _db_session() as db:
        if db is not None:
            from src.infrastructure.db.reference_data_repository import ReferenceDataRepository
            row = ReferenceDataRepository(db).get_by_instrument_id(instrument_id)
            if row is None:
                return json.dumps({
                    "found": False, "instrument_id": instrument_id,
                    "message": f"Instrument '{instrument_id}' not found in reference data.",
                })
            return json.dumps({
                "found": True, "instrument_id": row.instrument_id,
                "description": row.description, "asset_class": row.asset_class,
                "is_active": row.is_active,
            })

    ref = mock_store.get_reference(instrument_id)
    if ref is None:
        return json.dumps({
            "found": False, "instrument_id": instrument_id,
            "message": f"Instrument '{instrument_id}' not found in reference data.",
        })
    return json.dumps({
        "found": True, "instrument_id": ref.instrument_id,
        "description": ref.description, "asset_class": ref.asset_class,
        "is_active": ref.is_active,
    })


@tool
def get_counterparty(lei: str) -> str:
    """Look up counterparty master data by LEI (Legal Entity Identifier).

    Returns counterparty name, BIC, and active status.
    Returns an error message if the LEI is not found.
    """
    with _db_session() as db:
        if db is not None:
            from src.infrastructure.db.counterparty_repository import CounterpartyRepository
            row = CounterpartyRepository(db).get_by_lei(lei)
            if row is None:
                return json.dumps({
                    "found": False, "lei": lei,
                    "message": f"Counterparty with LEI '{lei}' not found in master data.",
                })
            return json.dumps({
                "found": True, "lei": row.lei, "name": row.name,
                "bic": row.bic, "is_active": row.is_active,
            })

    cp = mock_store.get_counterparty(lei)
    if cp is None:
        return json.dumps({
            "found": False, "lei": lei,
            "message": f"Counterparty with LEI '{lei}' not found in master data.",
        })
    return json.dumps({
        "found": True, "lei": cp.lei, "name": cp.name,
        "bic": cp.bic, "is_active": cp.is_active,
    })


@tool
def lookup_external_ssi(lei: str, currency: str) -> str:
    """Look up SSI from an external data source (Bloomberg/Omgeo equivalent).

    Used when no internal SSI is registered. If found, the data can be
    registered internally — but registration requires HITL approval.
    Returns not_found if the external source also has no SSI.
    """
    with _db_session() as db:
        if db is not None:
            from src.infrastructure.db.ssi_repository import SsiRepository
            row = SsiRepository(db).get(lei, currency, is_external=True)
            if row is None:
                return json.dumps({
                    "found": False, "lei": lei, "currency": currency,
                    "message": f"No SSI found in external source for LEI '{lei}' / currency '{currency}'.",
                })
            return json.dumps({
                "found": True, "source": "external",
                "lei": row.lei, "currency": row.currency,
                "bic": row.bic, "account": row.account, "iban": row.iban,
            })

    ssi = mock_store.get_external_ssi(lei, currency)
    if ssi is None:
        return json.dumps({
            "found": False, "lei": lei, "currency": currency,
            "message": f"No SSI found in external source for LEI '{lei}' / currency '{currency}'.",
        })
    return json.dumps({
        "found": True, "source": "external",
        "lei": ssi.lei, "currency": ssi.currency,
        "bic": ssi.bic, "account": ssi.account, "iban": ssi.iban,
    })


# ---------------------------------------------------------------------------
# Additional read-only tools (Phase 24-A)
# ---------------------------------------------------------------------------


@tool
def get_triage_history(trade_id: str) -> str:
    """Look up past completed triage results for a given trade ID.

    Returns up to 5 most recent triage runs with root_cause, diagnosis, and
    recommended_action. Useful for identifying recurring issues.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"found": False, "trade_id": trade_id, "history": [],
                               "message": "Triage history unavailable (no database)."})
        from src.infrastructure.db.models import TriageRunModel
        rows = (
            db.query(TriageRunModel)
            .filter(TriageRunModel.trade_id == trade_id,
                    TriageRunModel.status == "COMPLETED")
            .order_by(TriageRunModel.created_at.desc())
            .limit(5)
            .all()
        )
        if not rows:
            return json.dumps({"found": False, "trade_id": trade_id, "history": [],
                               "message": "No completed triage history found for this trade."})
        history = [
            {
                "root_cause": r.root_cause,
                "diagnosis": r.diagnosis,
                "recommended_action": r.recommended_action,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
        return json.dumps({"found": True, "trade_id": trade_id,
                           "count": len(history), "history": history})


@tool
def get_counterparty_exception_history(lei: str) -> str:
    """Get recent STP failure history for a counterparty LEI (last 30 days).

    Returns the count and details of recent exceptions. If 3 or more failures
    are found in 30 days, this indicates a systemic counterparty issue.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"lei": lei, "failure_count": 0, "period_days": 30,
                               "exceptions": [], "message": "History unavailable (no database)."})
        from src.infrastructure.db.models import StpExceptionModel, TradeModel
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        rows = (
            db.query(StpExceptionModel)
            .join(TradeModel, TradeModel.trade_id == StpExceptionModel.trade_id)
            .filter(TradeModel.counterparty_lei == lei,
                    StpExceptionModel.created_at >= cutoff)
            .order_by(StpExceptionModel.created_at.desc())
            .limit(10)
            .all()
        )
        exceptions = [
            {"trade_id": r.trade_id, "error_message": r.error_message,
             "status": r.status, "created_at": r.created_at.isoformat()}
            for r in rows
        ]
        warning = (
            "WARNING: 3 or more failures in 30 days — possible systemic issue."
            if len(exceptions) >= 3 else ""
        )
        return json.dumps({"lei": lei, "failure_count": len(exceptions),
                           "period_days": 30, "exceptions": exceptions,
                           "warning": warning})


# ---------------------------------------------------------------------------
# Write tools — require HITL approval before invocation
# ---------------------------------------------------------------------------


@tool
def register_ssi(lei: str, currency: str, bic: str, account: str, iban: str = "") -> str:
    """Register SSI (Settlement Standing Instructions) for a counterparty/currency pair
    in the internal SSI database.

    WARNING: This tool modifies the SSI database. It must only be called
    after explicit operator approval (HITL).

    Args:
        lei: Legal Entity Identifier of the counterparty.
        currency: Settlement currency code (e.g. 'USD').
        bic: BIC code of the receiving institution (8 or 11 characters).
        account: Account number or SWIFT account identifier.
        iban: IBAN (optional).
    """
    ssi = SettlementInstruction(
        lei=lei, currency=currency, bic=bic, account=account, iban=iban or None,
    )

    with _db_session() as db:
        if db is not None:
            from src.infrastructure.db.ssi_repository import SsiRepository
            SsiRepository(db).register(ssi, is_external=False)
            return json.dumps({
                "success": True,
                "message": f"SSI registered for LEI '{lei}' / currency '{currency}'.",
                "bic": bic, "account": account,
            })

    # Fallback: mock_store
    mock_store.register_ssi(ssi)
    return json.dumps({
        "success": True,
        "message": f"SSI registered for LEI '{lei}' / currency '{currency}'.",
        "bic": bic, "account": account,
    })


@tool
def reactivate_counterparty(lei: str) -> str:
    """Reactivate an inactive counterparty by setting is_active = True.

    WARNING: This modifies counterparty master data. Requires HITL approval.

    Args:
        lei: Legal Entity Identifier of the counterparty to reactivate.
    """
    with _db_session() as db:
        if db is not None:
            from src.infrastructure.db.counterparty_repository import CounterpartyRepository
            row = CounterpartyRepository(db).update(lei, name=None, bic=None, is_active=True)
            if row is None:
                return json.dumps({"success": False,
                                   "message": f"Counterparty '{lei}' not found."})
            return json.dumps({"success": True, "lei": lei, "is_active": True,
                               "message": f"Counterparty '{lei}' reactivated successfully."})
    return json.dumps({"success": True, "lei": lei,
                       "message": f"Counterparty '{lei}' reactivated (mock)."})


@tool
def update_ssi(lei: str, currency: str, bic: str = "",
               account: str = "", iban: str = "") -> str:
    """Update fields of an existing internal SSI (BIC, account, or IBAN).

    WARNING: This modifies settlement instructions. Requires HITL approval.
    Only fields with non-empty values are updated.

    Args:
        lei: Legal Entity Identifier of the counterparty.
        currency: Settlement currency code (e.g. 'EUR').
        bic: New BIC (leave empty to keep current value).
        account: New account number (leave empty to keep current value).
        iban: New IBAN (leave empty to keep current value).
    """
    with _db_session() as db:
        if db is not None:
            from src.infrastructure.db.ssi_repository import SsiRepository
            repo = SsiRepository(db)
            row = repo.get(lei, currency, is_external=False)
            if row is None:
                return json.dumps({"success": False,
                                   "message": f"No SSI found for LEI '{lei}' / currency '{currency}'."})
            if bic:
                row.bic = bic
            if account:
                row.account = account
            if iban:
                row.iban = iban
            row.updated_at = datetime.now(timezone.utc)
            db.commit()
            return json.dumps({
                "success": True, "lei": lei, "currency": currency,
                "bic": row.bic, "account": row.account, "iban": row.iban,
                "message": f"SSI updated for LEI '{lei}' / currency '{currency}'.",
            })
    return json.dumps({"success": False, "message": "Database not available."})


@tool
def escalate(trade_id: str, reason: str) -> str:
    """Escalate this triage case to a senior operator for manual resolution.

    Use when the root cause cannot be determined after full investigation.
    Requires HITL acknowledgment from the operator.

    Args:
        trade_id: The trade being escalated.
        reason: Explanation of why automated resolution is not possible.
    """
    return json.dumps({
        "escalated": True,
        "trade_id": trade_id,
        "reason": reason,
        "message": (
            f"Case {trade_id} has been escalated to a senior operator. "
            f"Reason: {reason}"
        ),
    })


# ---------------------------------------------------------------------------
# Tool lists (exported for use in the LangGraph agent)
# ---------------------------------------------------------------------------

READ_ONLY_TOOLS = [
    get_trade_detail,
    get_settlement_instructions,
    get_reference_data,
    get_counterparty,
    lookup_external_ssi,
    get_triage_history,
    get_counterparty_exception_history,
]

WRITE_TOOLS = [register_ssi, reactivate_counterparty, update_ssi, escalate]

ALL_TOOLS = READ_ONLY_TOOLS + WRITE_TOOLS
