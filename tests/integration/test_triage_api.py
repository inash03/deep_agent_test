"""Integration tests for the triage API endpoints.

These tests invoke the real LangGraph agent with a real LLM call.
They are skipped automatically when ANTHROPIC_API_KEY is not set.

Run only integration tests:
    pytest -m integration

Skip integration tests (fast unit-only run):
    pytest -m "not integration"
"""

import os

import pytest
from fastapi.testclient import TestClient

from src.main import app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set — skipping integration tests")
    return TestClient(app)


# ---------------------------------------------------------------------------
# POST /api/v1/triage — TRD-002: BIC_FORMAT_ERROR (no HITL)
# ---------------------------------------------------------------------------


class TestTriageCompleted:
    def test_bic_format_error_diagnosis(self, client):
        """TRD-002 has a malformed BIC in its SSI → agent should diagnose BIC_FORMAT_ERROR."""
        response = client.post(
            "/api/v1/triage",
            json={
                "trade_id": "TRD-002",
                "error_message": "SETT FAIL - BIC validation error for counterparty 5493001KJTIIGC8Y1R12",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "COMPLETED"
        assert body["root_cause"] == "BIC_FORMAT_ERROR"
        assert body["diagnosis"]
        assert body["recommended_action"]
        assert len(body["steps"]) > 0

    def test_counterparty_not_found_diagnosis(self, client):
        """TRD-003 has an unknown LEI → agent should diagnose COUNTERPARTY_NOT_FOUND."""
        response = client.post(
            "/api/v1/triage",
            json={
                "trade_id": "TRD-003",
                "error_message": "SETT FAIL - Counterparty LEI UNKNOWNLEI000000001 not found",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "COMPLETED"
        assert body["root_cause"] == "COUNTERPARTY_NOT_FOUND"


# ---------------------------------------------------------------------------
# POST /api/v1/triage — TRD-001: MISSING_SSI with HITL
# ---------------------------------------------------------------------------


class TestTriageHITL:
    def test_missing_ssi_triggers_pending_approval(self, client):
        """TRD-001 has no internal SSI but external source has data → PENDING_APPROVAL."""
        response = client.post(
            "/api/v1/triage",
            json={
                "trade_id": "TRD-001",
                "error_message": "SETT FAIL - SSI not found for counterparty LEI 213800QILIUD4ROSUO03",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "PENDING_APPROVAL"
        assert body["run_id"] is not None
        assert body["pending_action_description"] is not None
        return body["run_id"]

    def test_hitl_approve_completes_with_action_taken(self, client):
        """Approving HITL should complete the run with action_taken=True."""
        # Start triage for TRD-001
        start_resp = client.post(
            "/api/v1/triage",
            json={
                "trade_id": "TRD-001",
                "error_message": "SETT FAIL - SSI not found for counterparty LEI 213800QILIUD4ROSUO03",
            },
        )
        assert start_resp.status_code == 200
        run_id = start_resp.json()["run_id"]
        assert run_id is not None

        # Approve
        resume_resp = client.post(
            f"/api/v1/triage/{run_id}/resume",
            json={"approved": True},
        )
        assert resume_resp.status_code == 200
        body = resume_resp.json()
        assert body["status"] == "COMPLETED"
        assert body["action_taken"] is True
        assert body["root_cause"] == "MISSING_SSI"

    def test_hitl_reject_completes_without_action(self, client):
        """Rejecting HITL should complete the run with action_taken=False."""
        # Start a fresh triage for TRD-001
        start_resp = client.post(
            "/api/v1/triage",
            json={
                "trade_id": "TRD-001",
                "error_message": "SETT FAIL - SSI not found for counterparty LEI 213800QILIUD4ROSUO03",
            },
        )
        assert start_resp.status_code == 200
        run_id = start_resp.json()["run_id"]

        # Reject
        resume_resp = client.post(
            f"/api/v1/triage/{run_id}/resume",
            json={"approved": False},
        )
        assert resume_resp.status_code == 200
        body = resume_resp.json()
        assert body["status"] == "COMPLETED"
        assert body["action_taken"] is False

    def test_resume_unknown_run_id_returns_404(self, client):
        response = client.post(
            "/api/v1/triage/nonexistent-run-id/resume",
            json={"approved": True},
        )
        assert response.status_code == 404
