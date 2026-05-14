"""Trade Event lifecycle state machine tests (FR-08).

Verifies the AMEND / CANCEL lifecycle without a real database:

  create  → trade enters EventPending, event is FoUserToValidate
  FO ✓    → event advances to FoValidated
  FO ✗    → event → Cancelled; pending AMEND version removed
  BO ✓    → event → Done; AMEND activates new version / CANCEL sets Cancelled
  BO ✗    → event → Cancelled; pending AMEND version removed

All repository dependencies are replaced with MagicMock / SimpleNamespace.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.presentation.routers.trade_events import (
    bo_approve_event,
    create_trade_event,
    fo_approve_event,
)
from src.presentation.schemas import EventApproveRequest, TradeEventCreateRequest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)


def _event(**kwargs) -> SimpleNamespace:
    defaults = dict(
        id=uuid.uuid4(),
        trade_id="TRD-001",
        from_version=1,
        to_version=2,
        event_type="AMEND",
        workflow_status="FoUserToValidate",
        requested_by="fo_user_01",
        reason="Correct value date",
        amended_fields={"value_date": "2026-05-10"},
        created_at=_NOW,
        updated_at=_NOW,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _current_trade(version: int = 1, status: str = "Initial") -> SimpleNamespace:
    return SimpleNamespace(trade_id="TRD-001", version=version, workflow_status=status, is_current=True)


# ---------------------------------------------------------------------------
# create_trade_event — AMEND
# ---------------------------------------------------------------------------


def test_amend_event_creation_sets_trade_to_event_pending() -> None:
    """FR-08: AMEND event creation transitions the trade to EventPending."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None  # no existing pending version

    body = TradeEventCreateRequest(
        event_type="AMEND",
        reason="Correct value date",
        requested_by="fo_user_01",
        amended_fields={"value_date": "2026-05-10"},
    )
    new_version = _current_trade(version=2)
    evt = _event()

    with (
        patch("src.presentation.routers.trade_events.TradeRepository") as MockTR,
        patch("src.presentation.routers.trade_events.TradeEventRepository") as MockER,
    ):
        tr = MockTR.return_value
        er = MockER.return_value
        tr.get_current.return_value = _current_trade()
        er.get_pending.return_value = None
        tr.create_next_version.return_value = new_version
        er.create.return_value = evt

        result = create_trade_event("TRD-001", body, db=db)

    tr.update_workflow_status.assert_called_once_with("TRD-001", "EventPending")
    assert result.event_type == "AMEND"


def test_amend_event_creation_creates_new_trade_version() -> None:
    """FR-08: AMEND event must call create_next_version to build the pending version."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    body = TradeEventCreateRequest(
        event_type="AMEND",
        reason="Correct fx rate",
        requested_by="fo_user_01",
        amended_fields={"fx_rate": "1.09250000"},
    )
    new_version = _current_trade(version=2)
    evt = _event()

    with (
        patch("src.presentation.routers.trade_events.TradeRepository") as MockTR,
        patch("src.presentation.routers.trade_events.TradeEventRepository") as MockER,
    ):
        tr = MockTR.return_value
        er = MockER.return_value
        tr.get_current.return_value = _current_trade()
        er.get_pending.return_value = None
        tr.create_next_version.return_value = new_version
        er.create.return_value = evt

        create_trade_event("TRD-001", body, db=db)

    tr.create_next_version.assert_called_once_with("TRD-001", "AMEND", {"fx_rate": "1.09250000"})


# ---------------------------------------------------------------------------
# create_trade_event — CANCEL
# ---------------------------------------------------------------------------


def test_cancel_event_creation_sets_trade_to_event_pending_without_new_version() -> None:
    """FR-08: CANCEL does not create a new trade version — only sets EventPending."""
    db = MagicMock()
    body = TradeEventCreateRequest(
        event_type="CANCEL",
        reason="Trade cancelled by counterparty",
        requested_by="fo_user_01",
    )
    evt = _event(event_type="CANCEL", to_version=1)

    with (
        patch("src.presentation.routers.trade_events.TradeRepository") as MockTR,
        patch("src.presentation.routers.trade_events.TradeEventRepository") as MockER,
    ):
        tr = MockTR.return_value
        er = MockER.return_value
        tr.get_current.return_value = _current_trade()
        er.get_pending.return_value = None
        er.create.return_value = evt

        result = create_trade_event("TRD-001", body, db=db)

    tr.create_next_version.assert_not_called()
    tr.update_workflow_status.assert_called_once_with("TRD-001", "EventPending")
    assert result.event_type == "CANCEL"


# ---------------------------------------------------------------------------
# create_trade_event — error paths
# ---------------------------------------------------------------------------


def test_create_event_returns_404_when_trade_not_found() -> None:
    """FR-08: event creation fails with 404 when the trade does not exist."""
    db = MagicMock()
    body = TradeEventCreateRequest(
        event_type="CANCEL", reason="n/a", requested_by="fo_user_01"
    )

    with (
        patch("src.presentation.routers.trade_events.TradeRepository") as MockTR,
        patch("src.presentation.routers.trade_events.TradeEventRepository"),
    ):
        MockTR.return_value.get_current.return_value = None

        with pytest.raises(HTTPException) as exc:
            create_trade_event("TRD-UNKNOWN", body, db=db)

    assert exc.value.status_code == 404


def test_create_event_returns_409_when_pending_event_already_exists() -> None:
    """FR-08: only one in-flight event per trade is allowed."""
    db = MagicMock()
    body = TradeEventCreateRequest(
        event_type="CANCEL", reason="duplicate", requested_by="fo_user_01"
    )

    with (
        patch("src.presentation.routers.trade_events.TradeRepository") as MockTR,
        patch("src.presentation.routers.trade_events.TradeEventRepository") as MockER,
    ):
        MockTR.return_value.get_current.return_value = _current_trade()
        MockER.return_value.get_pending.return_value = _event()  # already in-flight

        with pytest.raises(HTTPException) as exc:
            create_trade_event("TRD-001", body, db=db)

    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# fo_approve_event
# ---------------------------------------------------------------------------


def test_fo_approval_transitions_event_to_fo_validated() -> None:
    """FR-08: FO approval moves the event to FoValidated for BO review."""
    db = MagicMock()
    evt = _event(workflow_status="FoUserToValidate")

    with (
        patch("src.presentation.routers.trade_events.TradeEventRepository") as MockER,
        patch("src.presentation.routers.trade_events._get_event_or_404", return_value=evt),
    ):
        er = MockER.return_value
        fo_approve_event(evt.id, EventApproveRequest(approved=True), db=db)

    er.update_status.assert_called_once_with(evt.id, "FoValidated")


def test_fo_rejection_cancels_event_and_removes_amend_version() -> None:
    """FR-08: FO rejection cancels the event and deletes the pending AMEND version."""
    db = MagicMock()
    evt = _event(workflow_status="FoUserToValidate", event_type="AMEND", to_version=2)

    with (
        patch("src.presentation.routers.trade_events.TradeEventRepository") as MockER,
        patch("src.presentation.routers.trade_events._get_event_or_404", return_value=evt),
        patch("src.presentation.routers.trade_events._cancel_pending_version") as mock_cancel,
        patch("src.presentation.routers.trade_events.TradeRepository"),
    ):
        er = MockER.return_value
        fo_approve_event(evt.id, EventApproveRequest(approved=False), db=db)

    er.update_status.assert_called_once_with(evt.id, "Cancelled")
    mock_cancel.assert_called_once_with(evt.trade_id, evt.to_version, db)


def test_fo_approve_returns_409_when_event_not_awaiting_fo() -> None:
    """FR-08: FO approval is only valid from FoUserToValidate state."""
    db = MagicMock()
    evt = _event(workflow_status="FoValidated")  # already past FO stage

    with (
        patch("src.presentation.routers.trade_events.TradeEventRepository"),
        patch("src.presentation.routers.trade_events._get_event_or_404", return_value=evt),
    ):
        with pytest.raises(HTTPException) as exc:
            fo_approve_event(evt.id, EventApproveRequest(approved=True), db=db)

    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# bo_approve_event
# ---------------------------------------------------------------------------


def test_bo_approval_of_amend_activates_new_trade_version() -> None:
    """FR-08: BO approval of AMEND activates the new version and marks it Initial."""
    db = MagicMock()
    evt = _event(workflow_status="FoValidated", event_type="AMEND", to_version=2)
    activated = SimpleNamespace(workflow_status="EventPending", trade_id="TRD-001", version=2)

    with (
        patch("src.presentation.routers.trade_events.TradeEventRepository") as MockER,
        patch("src.presentation.routers.trade_events.TradeRepository") as MockTR,
        patch("src.presentation.routers.trade_events._get_event_or_404", return_value=evt),
        patch("src.presentation.routers.trade_events.maybe_run_fo_check"),
    ):
        er = MockER.return_value
        MockTR.return_value.activate_version.return_value = activated

        bo_approve_event(evt.id, EventApproveRequest(approved=True), db=db)

    er.update_status.assert_called_once_with(evt.id, "Done")
    MockTR.return_value.activate_version.assert_called_once_with(evt.trade_id, evt.to_version)
    assert activated.workflow_status == "Initial"


def test_bo_approval_of_cancel_sets_trade_to_cancelled() -> None:
    """FR-08: BO approval of CANCEL sets the trade workflow_status to Cancelled."""
    db = MagicMock()
    evt = _event(workflow_status="FoValidated", event_type="CANCEL", to_version=1)

    with (
        patch("src.presentation.routers.trade_events.TradeEventRepository") as MockER,
        patch("src.presentation.routers.trade_events.TradeRepository") as MockTR,
        patch("src.presentation.routers.trade_events._get_event_or_404", return_value=evt),
    ):
        er = MockER.return_value
        tr = MockTR.return_value

        bo_approve_event(evt.id, EventApproveRequest(approved=True), db=db)

    er.update_status.assert_called_once_with(evt.id, "Done")
    tr.update_workflow_status.assert_called_once_with(evt.trade_id, "Cancelled")


def test_bo_rejection_of_amend_cancels_event_and_removes_pending_version() -> None:
    """FR-08: BO rejection cancels the event and removes the pending AMEND version."""
    db = MagicMock()
    evt = _event(workflow_status="FoValidated", event_type="AMEND", to_version=2)

    with (
        patch("src.presentation.routers.trade_events.TradeEventRepository") as MockER,
        patch("src.presentation.routers.trade_events.TradeRepository"),
        patch("src.presentation.routers.trade_events._get_event_or_404", return_value=evt),
        patch("src.presentation.routers.trade_events._cancel_pending_version") as mock_cancel,
    ):
        er = MockER.return_value
        bo_approve_event(evt.id, EventApproveRequest(approved=False), db=db)

    er.update_status.assert_called_once_with(evt.id, "Cancelled")
    mock_cancel.assert_called_once_with(evt.trade_id, evt.to_version, db)


def test_bo_approve_returns_409_when_event_not_fo_validated() -> None:
    """FR-08: BO approval is only valid from FoValidated state."""
    db = MagicMock()
    evt = _event(workflow_status="FoUserToValidate")  # hasn't passed FO yet

    with (
        patch("src.presentation.routers.trade_events.TradeEventRepository"),
        patch("src.presentation.routers.trade_events._get_event_or_404", return_value=evt),
    ):
        with pytest.raises(HTTPException) as exc:
            bo_approve_event(evt.id, EventApproveRequest(approved=True), db=db)

    assert exc.value.status_code == 409
