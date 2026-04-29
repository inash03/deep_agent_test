"""Unit tests for auto FO/BO triage triggers in rule_engine."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.infrastructure.rule_engine import _build_error_context, run_bo_check, run_fo_check


def test_build_error_context_uses_failed_rules_only() -> None:
    results = [
        SimpleNamespace(rule_name="ok_rule", passed=True, message="ok"),
        SimpleNamespace(rule_name="bad_rule", passed=False, message="failed for reason"),
    ]
    context = _build_error_context(results)  # type: ignore[arg-type]
    assert context == "[bad_rule] failed for reason"


def test_run_fo_check_auto_starts_fo_triage_on_failure() -> None:
    db = MagicMock()
    trade = SimpleNamespace(trade_id="TRD-001")
    repo = MagicMock()
    repo.get_current.return_value = trade

    setting_repo = MagicMock()
    setting_repo.get.return_value = SimpleNamespace(value="auto")
    triage_uc = MagicMock()

    with (
        patch("src.infrastructure.rule_engine.TradeRepository", return_value=repo),
        patch(
            "src.infrastructure.rule_engine.FO_RULES",
            [SimpleNamespace(rule_name="amount_positive", severity="error", check_fn=lambda _: (False, "Amount invalid"))],
        ),
        patch("src.infrastructure.rule_engine.AppSettingRepository", return_value=setting_repo),
        patch("src.infrastructure.rule_engine._get_fo_triage_use_case", return_value=triage_uc),
    ):
        results, status = run_fo_check("TRD-001", db)

    assert status == "FoAgentToCheck"
    assert len(results) == 1
    triage_uc.start.assert_called_once_with(
        trade_id="TRD-001",
        error_context="[amount_positive] Amount invalid",
    )


def test_run_bo_check_auto_starts_bo_triage_on_failure() -> None:
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    trade = SimpleNamespace(trade_id="TRD-002", counterparty_lei="LEI123", currency="USD")
    repo = MagicMock()
    repo.get_current.return_value = trade

    setting_repo = MagicMock()
    setting_repo.get.return_value = SimpleNamespace(value="auto")
    triage_uc = MagicMock()

    with (
        patch("src.infrastructure.rule_engine.TradeRepository", return_value=repo),
        patch(
            "src.infrastructure.rule_engine.BO_RULES",
            [
                SimpleNamespace(
                    rule_name="ssi_exists",
                    severity="error",
                    check_fn=lambda _trade, _cp, _ssi: (False, "No SSI"),
                )
            ],
        ),
        patch("src.infrastructure.rule_engine.AppSettingRepository", return_value=setting_repo),
        patch("src.infrastructure.rule_engine._get_bo_triage_use_case", return_value=triage_uc),
    ):
        results, status = run_bo_check("TRD-002", db)

    assert status == "BoAgentToCheck"
    assert len(results) == 1
    triage_uc.start.assert_called_once_with(
        trade_id="TRD-002",
        error_context="[ssi_exists] No SSI",
    )
