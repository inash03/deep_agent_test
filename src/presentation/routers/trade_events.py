"""FastAPI router for Trade Event lifecycle (Amend / Cancel).

Endpoints:
  GET  /api/v1/trades/{trade_id}/events          — list events for a trade
  POST /api/v1/trades/{trade_id}/events          — create new Amend/Cancel event
  PATCH /api/v1/trade-events/{event_id}/fo-approve — FO approve or reject
  PATCH /api/v1/trade-events/{event_id}/bo-approve — BO approve or reject

State machine (EventWorkflowStatus):
  Created      → FoUserToValidate
  FO approve   → FoValidated
  FO reject    → Cancelled  (pending trade version deleted)
  BO approve   → Done       (AMEND: new version activated; CANCEL: trade cancelled)
  BO reject    → Cancelled  (pending trade version deleted)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.infrastructure.db.models import TradeModel
from src.infrastructure.db.session import get_db
from src.infrastructure.db.trade_event_repository import TradeEventRepository
from src.infrastructure.db.trade_repository import TradeRepository
from src.presentation.dependencies import verify_api_key
from src.presentation.schemas import (
    EventApproveRequest,
    TradeEventCreateRequest,
    TradeEventListResponse,
    TradeEventOut,
)

router = APIRouter(prefix="/api/v1", tags=["trade-events"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_out(row) -> TradeEventOut:
    return TradeEventOut(
        id=row.id,
        trade_id=row.trade_id,
        from_version=row.from_version,
        to_version=row.to_version,
        event_type=row.event_type,
        workflow_status=row.workflow_status,
        requested_by=row.requested_by,
        reason=row.reason,
        amended_fields=row.amended_fields,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _get_event_or_404(event_id: uuid.UUID, db: Session):
    repo = TradeEventRepository(db)
    row = db.query(repo._db.get_bind().__class__) if False else None  # type hint placeholder
    from src.infrastructure.db.models import TradeEventModel
    row = db.query(TradeEventModel).filter(TradeEventModel.id == event_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    return row


def _cancel_pending_version(trade_id: str, to_version: int, db: Session) -> None:
    """Remove the EventPending trade version created for an AMEND event."""
    db.query(TradeModel).filter(
        TradeModel.trade_id == trade_id,
        TradeModel.version == to_version,
        TradeModel.is_current.is_(False),
    ).delete(synchronize_session=False)

    # Restore current version to its pre-EventPending workflow_status
    # (we don't track the previous status, so reset to FoAgentToCheck as a safe default)
    trade_repo = TradeRepository(db)
    current = trade_repo.get_current(trade_id)
    if current and current.workflow_status == "EventPending":
        current.workflow_status = "FoAgentToCheck"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/trades/{trade_id}/events",
    response_model=TradeEventListResponse,
    summary="List trade events",
)
def list_trade_events(
    trade_id: str,
    db: Session = Depends(get_db),
) -> TradeEventListResponse:
    rows = TradeEventRepository(db).list_for_trade(trade_id)
    return TradeEventListResponse(items=[_to_out(r) for r in rows], total=len(rows))


@router.post(
    "/trades/{trade_id}/events",
    response_model=TradeEventOut,
    status_code=201,
    summary="Create a new Amend or Cancel event",
    description=(
        "Creates an Amend or Cancel event for a trade. "
        "AMEND also creates a new pending trade version with the amended field values. "
        "The event starts in FoUserToValidate status awaiting FO approval."
    ),
)
def create_trade_event(
    trade_id: str,
    body: TradeEventCreateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> TradeEventOut:
    if body.event_type not in ("AMEND", "CANCEL"):
        raise HTTPException(status_code=422, detail="event_type must be AMEND or CANCEL.")
    if body.event_type == "AMEND" and not body.amended_fields:
        raise HTTPException(status_code=422, detail="amended_fields is required for AMEND events.")

    trade_repo = TradeRepository(db)
    current = trade_repo.get_current(trade_id)
    if current is None:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found.")

    # Check for in-flight event
    existing = TradeEventRepository(db).get_pending(trade_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Trade '{trade_id}' already has a pending event ({existing.id}).",
        )

    from_version = current.version

    if body.event_type == "AMEND":
        # Guard against agent-created pending versions (not tracked in trade_events table).
        # FoAgent's create_amend_event tool calls create_next_version directly, so the
        # UNIQUE(trade_id, version) constraint would fire without this check.
        pending_ver = (
            db.query(TradeModel)
            .filter(
                TradeModel.trade_id == trade_id,
                TradeModel.is_current.is_(False),
                TradeModel.workflow_status == "EventPending",
            )
            .first()
        )
        if pending_ver:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Trade '{trade_id}' already has a pending amendment version v{pending_ver.version} "
                    "created by the triage agent. The agent flow must complete before a manual event can be created."
                ),
            )
        new_row = trade_repo.create_next_version(trade_id, "AMEND", body.amended_fields)
        to_version = new_row.version
        trade_repo.update_workflow_status(trade_id, "EventPending")
    else:  # CANCEL — no new version needed
        to_version = from_version
        trade_repo.update_workflow_status(trade_id, "EventPending")

    event = TradeEventRepository(db).create(
        trade_id=trade_id,
        from_version=from_version,
        to_version=to_version,
        event_type=body.event_type,
        requested_by=body.requested_by,
        reason=body.reason,
        amended_fields=body.amended_fields,
    )
    db.commit()
    db.refresh(event)
    return _to_out(event)


@router.patch(
    "/trade-events/{event_id}/fo-approve",
    response_model=TradeEventOut,
    summary="FO approve or reject an event",
    description=(
        "FO approval transitions the event to FoValidated (ready for BO review). "
        "FO rejection cancels the event and reverts the trade status."
    ),
)
def fo_approve_event(
    event_id: uuid.UUID,
    body: EventApproveRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> TradeEventOut:
    event = _get_event_or_404(event_id, db)

    if event.workflow_status != "FoUserToValidate":
        raise HTTPException(
            status_code=409,
            detail=f"Event is in '{event.workflow_status}', not FoUserToValidate.",
        )

    event_repo = TradeEventRepository(db)

    if body.approved:
        event_repo.update_status(event_id, "FoValidated")
    else:
        event_repo.update_status(event_id, "Cancelled")
        if event.event_type == "AMEND":
            _cancel_pending_version(event.trade_id, event.to_version, db)

    db.commit()
    db.refresh(event)
    return _to_out(event)


@router.patch(
    "/trade-events/{event_id}/bo-approve",
    response_model=TradeEventOut,
    summary="BO approve or reject an event",
    description=(
        "BO approval finalises the event (Done). "
        "AMEND: activates the new trade version with workflow_status=Initial. "
        "CANCEL: sets the trade workflow_status to Cancelled. "
        "BO rejection cancels the event and reverts the trade status."
    ),
)
def bo_approve_event(
    event_id: uuid.UUID,
    body: EventApproveRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> TradeEventOut:
    event = _get_event_or_404(event_id, db)

    if event.workflow_status != "FoValidated":
        raise HTTPException(
            status_code=409,
            detail=f"Event is in '{event.workflow_status}', not FoValidated.",
        )

    trade_repo = TradeRepository(db)
    event_repo = TradeEventRepository(db)

    if body.approved:
        event_repo.update_status(event_id, "Done")
        if event.event_type == "AMEND":
            # Activate the new version and restart the FO workflow
            activated = trade_repo.activate_version(event.trade_id, event.to_version)
            if activated:
                activated.workflow_status = "Initial"
        else:  # CANCEL
            trade_repo.update_workflow_status(event.trade_id, "Cancelled")
    else:
        event_repo.update_status(event_id, "Cancelled")
        if event.event_type == "AMEND":
            _cancel_pending_version(event.trade_id, event.to_version, db)

    db.commit()
    db.refresh(event)
    return _to_out(event)
