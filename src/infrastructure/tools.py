"""LangGraph tools for the STP Exception Triage Agent.

Data source selection:
  - If DATABASE_URL is set → reads from PostgreSQL via repositories (production)
  - Otherwise            → reads from in-memory mock_store (unit tests / dev without DB)

BoAgent tools (13):
  Read-only / non-HITL:
    get_trade_detail, get_counterparty, get_settlement_instructions,
    lookup_external_ssi, get_triage_history, get_counterparty_exception_history,
    get_bo_check_results, get_fo_explanation, escalate_to_bo_user

  HITL write (requires operator approval):
    register_ssi, reactivate_counterparty, update_ssi, send_back_to_fo

FoAgent tools (9):
  Read-only / non-HITL:
    get_fo_check_results, get_bo_sendback_reason, get_trade_detail,
    get_counterparty, get_reference_data, provide_explanation, escalate_to_fo_user

  HITL write (requires operator approval):
    create_amend_event, create_cancel_event
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
    currency, amount, value date, settlement currency, workflow_status,
    and sendback_count.
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
                "version": row.version,
                "workflow_status": row.workflow_status,
                "sendback_count": row.sendback_count,
                "counterparty_lei": row.counterparty_lei,
                "instrument_id": row.instrument_id,
                "currency": row.currency,
                "amount": str(row.amount),
                "trade_date": row.trade_date.isoformat(),
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
# BoAgent read-only tools (Phase 26-C)
# ---------------------------------------------------------------------------


@tool
def get_bo_check_results(trade_id: str) -> str:
    """Retrieve the stored BoCheck rule results for a trade.

    Returns the list of rule results (passed/failed + message) plus the
    current workflow_status and sendback_count.
    Call this first in BoAgent triage to understand which rules failed.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        trade = TradeRepository(db).get_current(trade_id)
        if trade is None:
            return json.dumps({"error": f"Trade '{trade_id}' not found."})
        if trade.bo_check_results is None:
            return json.dumps({
                "trade_id": trade_id,
                "found": False,
                "workflow_status": trade.workflow_status,
                "sendback_count": trade.sendback_count,
                "message": "No BoCheck results available. BoCheck has not been run yet.",
            })
        return json.dumps({
            "trade_id": trade_id,
            "found": True,
            "workflow_status": trade.workflow_status,
            "sendback_count": trade.sendback_count,
            "results": trade.bo_check_results,
        })


@tool
def get_fo_explanation(trade_id: str) -> str:
    """Retrieve the FoAgent's explanation recorded when transitioning to FoValidated.

    Available only on 2nd BoAgent triage (after a send_back_to_fo cycle).
    Returns the FoAgent's rationale for why the trade content is correct
    despite the BoCheck concerns.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        trade = TradeRepository(db).get_current(trade_id)
        if trade is None:
            return json.dumps({"error": f"Trade '{trade_id}' not found."})
        if not trade.fo_explanation:
            return json.dumps({
                "trade_id": trade_id,
                "found": False,
                "message": "No FoAgent explanation recorded for this trade.",
            })
        return json.dumps({
            "trade_id": trade_id,
            "found": True,
            "fo_explanation": trade.fo_explanation,
        })


# ---------------------------------------------------------------------------
# BoAgent write tools — HITL or immediate
# ---------------------------------------------------------------------------


@tool
def send_back_to_fo(trade_id: str, reason: str) -> str:
    """Send the trade back to FoAgent for re-investigation.

    Use ONLY when the root cause is clearly FO-side (e.g. bad value date,
    wrong instrument, amount error) and sendback_count == 0.
    WARNING: Requires HITL operator approval.
    Cannot be called a second time for the same trade — use escalate_to_bo_user instead.

    Args:
        trade_id: The trade to send back.
        reason: Clear explanation of what FO needs to fix.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"success": False, "error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        repo = TradeRepository(db)
        trade = repo.get_current(trade_id)
        if trade is None:
            return json.dumps({"success": False, "error": f"Trade '{trade_id}' not found."})
        new_count = trade.sendback_count + 1
        repo.update_workflow_status(
            trade_id, "FoAgentToCheck",
            bo_sendback_reason=reason,
            sendback_count=new_count,
        )
        db.commit()
        return json.dumps({
            "success": True,
            "trade_id": trade_id,
            "new_status": "FoAgentToCheck",
            "sendback_count": new_count,
            "message": f"Trade '{trade_id}' sent back to FoAgent (sendback #{new_count}). Reason: {reason}",
        })


@tool
def escalate_to_bo_user(trade_id: str, reason: str) -> str:
    """Escalate the trade to a BO User for manual resolution.

    Use when: the issue is unfixable by BoAgent alone, a 2nd sendback would
    be needed (prohibited), or the root cause requires human judgment.

    Args:
        trade_id: The trade to escalate.
        reason: Explanation of why automated resolution is not possible.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"success": False, "error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        repo = TradeRepository(db)
        row = repo.update_workflow_status(trade_id, "BoUserToValidate")
        if row is None:
            return json.dumps({"success": False, "error": f"Trade '{trade_id}' not found."})
        db.commit()
        return json.dumps({
            "success": True,
            "trade_id": trade_id,
            "new_status": "BoUserToValidate",
            "message": f"Trade '{trade_id}' escalated to BO User. Reason: {reason}",
        })


# ---------------------------------------------------------------------------
# FoAgent read-only tools (Phase 26-D)
# ---------------------------------------------------------------------------


@tool
def get_fo_check_results(trade_id: str) -> str:
    """Retrieve the stored FoCheck rule results for a trade.

    Returns the list of rule results (passed/failed + message) plus the
    current workflow_status and sendback_count.
    Call this first in FoAgent triage to understand which rules failed.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        trade = TradeRepository(db).get_current(trade_id)
        if trade is None:
            return json.dumps({"error": f"Trade '{trade_id}' not found."})
        if trade.fo_check_results is None:
            return json.dumps({
                "trade_id": trade_id,
                "found": False,
                "workflow_status": trade.workflow_status,
                "sendback_count": trade.sendback_count,
                "message": "No FoCheck results available. FoCheck has not been run yet.",
            })
        return json.dumps({
            "trade_id": trade_id,
            "found": True,
            "workflow_status": trade.workflow_status,
            "sendback_count": trade.sendback_count,
            "results": trade.fo_check_results,
        })


@tool
def get_bo_sendback_reason(trade_id: str) -> str:
    """Retrieve the reason BoAgent sent this trade back to FO.

    Only available when sendback_count >= 1.
    Contains BoAgent's explanation of what FO-side issue it identified
    and what FO needs to correct or clarify.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        trade = TradeRepository(db).get_current(trade_id)
        if trade is None:
            return json.dumps({"error": f"Trade '{trade_id}' not found."})
        if not trade.bo_sendback_reason:
            return json.dumps({
                "trade_id": trade_id,
                "found": False,
                "message": "No BO sendback reason recorded. This trade was not sent back by BO.",
            })
        return json.dumps({
            "trade_id": trade_id,
            "found": True,
            "bo_sendback_reason": trade.bo_sendback_reason,
            "sendback_count": trade.sendback_count,
        })


# ---------------------------------------------------------------------------
# FoAgent write tools — HITL or immediate (Phase 26-D)
# ---------------------------------------------------------------------------


@tool
def create_amend_event(trade_id: str, reason: str, amended_fields: str) -> str:
    """Propose a trade amendment to correct FO-side data errors.

    WARNING: Requires HITL operator approval. Creates a new pending version
    with the corrected field values.

    Args:
        trade_id: The trade to amend.
        reason: Why the amendment is needed.
        amended_fields: JSON string of field:new_value pairs to change.
            Supported fields: value_date (YYYY-MM-DD), trade_date (YYYY-MM-DD),
            amount (decimal string), currency, settlement_currency, instrument_id.
            Example: '{"value_date": "2026-05-01", "amount": "1000000.00"}'
    """
    import json as _json
    if isinstance(amended_fields, dict):
        fields: dict = amended_fields
    elif amended_fields:
        try:
            fields = _json.loads(amended_fields)
        except (_json.JSONDecodeError, TypeError):
            return json.dumps({"success": False, "error": f"amended_fields is not valid JSON: {amended_fields}"})
    else:
        fields = {}

    with _db_session() as db:
        if db is None:
            return json.dumps({"success": False, "error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        from src.infrastructure.db.trade_event_repository import TradeEventRepository
        repo = TradeRepository(db)
        try:
            current = repo.get_current(trade_id)
            if current is None:
                return json.dumps({"success": False, "error": f"Trade '{trade_id}' not found."})
            new_row = repo.create_next_version(trade_id, "AMEND", fields)
            repo.update_workflow_status(trade_id, "EventPending")
            event = TradeEventRepository(db).create(
                trade_id=trade_id,
                from_version=current.version,
                to_version=new_row.version,
                event_type="AMEND",
                requested_by="fo_agent",
                reason=reason,
                amended_fields=fields,
            )
            db.commit()
            return json.dumps({
                "success": True,
                "trade_id": trade_id,
                "new_version": new_row.version,
                "event_id": str(event.id),
                "amended_fields": fields,
                "message": (
                    f"Amendment proposed for trade '{trade_id}' (version {new_row.version}). "
                    "Awaiting FO/BO operator approval. Reason: " + reason
                ),
            })
        except ValueError as exc:
            return json.dumps({"success": False, "error": str(exc)})


@tool
def create_cancel_event(trade_id: str, reason: str) -> str:
    """Propose cancellation of the trade.

    WARNING: Requires HITL operator approval. Transitions the trade to Cancelled
    when the trade is fundamentally erroneous and cannot be settled.

    Args:
        trade_id: The trade to cancel.
        reason: Detailed explanation of why the trade must be cancelled.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"success": False, "error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        from src.infrastructure.db.trade_event_repository import TradeEventRepository
        repo = TradeRepository(db)
        current = repo.get_current(trade_id)
        if current is None:
            return json.dumps({"success": False, "error": f"Trade '{trade_id}' not found."})
        repo.update_workflow_status(trade_id, "EventPending")
        event = TradeEventRepository(db).create(
            trade_id=trade_id,
            from_version=current.version,
            to_version=current.version,
            event_type="CANCEL",
            requested_by="fo_agent",
            reason=reason,
            amended_fields=None,
        )
        db.commit()
        return json.dumps({
            "success": True,
            "trade_id": trade_id,
            "event_id": str(event.id),
            "message": (
                f"Cancellation proposed for trade '{trade_id}'. "
                "Awaiting FO/BO operator approval. Reason: " + reason
            ),
        })


@tool
def provide_explanation(trade_id: str, explanation: str) -> str:
    """Record FO's explanation and transition the trade to FoValidated.

    Use when BoAgent sent the trade back but the trade data IS correct —
    the issue is on the BO/SSI/counterparty side, not FO data.
    FoValidated allows BoAgent to retry triage with the explanation context.

    Args:
        trade_id: The trade to mark as FoValidated.
        explanation: FO's explanation of why the trade content is correct
            and what BO should focus on instead.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"success": False, "error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        repo = TradeRepository(db)
        row = repo.update_workflow_status(trade_id, "FoValidated", fo_explanation=explanation)
        if row is None:
            return json.dumps({"success": False, "error": f"Trade '{trade_id}' not found."})
        db.commit()
        return json.dumps({
            "success": True,
            "trade_id": trade_id,
            "new_status": "FoValidated",
            "fo_explanation": explanation,
            "message": f"Trade '{trade_id}' marked FoValidated with FO explanation.",
        })


@tool
def escalate_to_fo_user(trade_id: str, reason: str) -> str:
    """Escalate the trade to a FO User for manual resolution.

    Use when FoAgent cannot determine the correct fix, the issue is ambiguous,
    or multiple complex problems require senior judgment.

    Args:
        trade_id: The trade to escalate.
        reason: Explanation of why automated resolution is not possible.
    """
    with _db_session() as db:
        if db is None:
            return json.dumps({"success": False, "error": "Database not available."})
        from src.infrastructure.db.trade_repository import TradeRepository
        repo = TradeRepository(db)
        row = repo.update_workflow_status(trade_id, "FoUserToValidate")
        if row is None:
            return json.dumps({"success": False, "error": f"Trade '{trade_id}' not found."})
        db.commit()
        return json.dumps({
            "success": True,
            "trade_id": trade_id,
            "new_status": "FoUserToValidate",
            "message": f"Trade '{trade_id}' escalated to FO User. Reason: {reason}",
        })


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
# RAG tool — semantic search over past triage cases and SWIFT knowledge
# ---------------------------------------------------------------------------


@tool
def search_similar_triage_cases(query: str) -> str:
    """Search historical triage cases and SWIFT knowledge semantically similar to the query.

    Use this when investigating an unfamiliar failure pattern to find past resolutions.
    Provide a description combining the error code, failed rules, and symptoms.
    Returns up to 3 similar past cases with their diagnoses, root causes, and outcomes.

    Args:
        query: Description of the current error (e.g. "AG01 counterparty inactive failed rule counterparty_active").
    """
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("DATABASE_URL"):
        return json.dumps({"found": False, "message": "RAG service not configured (OPENAI_API_KEY or DATABASE_URL missing)."})
    try:
        from src.infrastructure.rag_service import _rag_service
        results = _rag_service.search_similar(query, k=3)
        if not results:
            return json.dumps({"found": False, "message": "No similar cases found in knowledge base."})
        return json.dumps({"found": True, "count": len(results), "similar_cases": results})
    except Exception as exc:
        return json.dumps({"found": False, "error": str(exc)})


# ---------------------------------------------------------------------------
# Tool lists (exported for use in the LangGraph agents)
# ---------------------------------------------------------------------------

# Legacy tool lists (kept for backward compatibility with old /api/v1/triage)
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

# BoAgent tool lists (Phase 26-C)
BO_READ_ONLY_TOOLS = [
    get_trade_detail,
    get_counterparty,
    get_settlement_instructions,
    lookup_external_ssi,
    get_triage_history,
    get_counterparty_exception_history,
    get_bo_check_results,
    get_fo_explanation,
    escalate_to_bo_user,  # non-HITL write — executed immediately
]

BO_HITL_TOOLS = [
    register_ssi,
    reactivate_counterparty,
    update_ssi,
    send_back_to_fo,
]

BO_ALL_TOOLS = BO_READ_ONLY_TOOLS + BO_HITL_TOOLS

# FoAgent tool lists (Phase 26-D)
FO_READ_ONLY_TOOLS = [
    get_fo_check_results,
    get_bo_sendback_reason,
    get_trade_detail,
    get_counterparty,
    get_reference_data,
    search_similar_triage_cases,  # RAG: semantic search over past cases and SWIFT knowledge
    provide_explanation,     # non-HITL write — executed immediately
    escalate_to_fo_user,     # non-HITL write — executed immediately
]

FO_HITL_TOOLS = [
    create_amend_event,
    create_cancel_event,
]

FO_ALL_TOOLS = FO_READ_ONLY_TOOLS + FO_HITL_TOOLS
