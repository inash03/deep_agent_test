"""Unit tests for seed auto FoCheck behavior."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.infrastructure.seed import _maybe_auto_run_fo_check


def _mock_db_with_trigger(value: str | None) -> MagicMock:
    db = MagicMock()
    setting = None if value is None else SimpleNamespace(value=value)
    db.query.return_value.filter.return_value.first.return_value = setting
    return db


def test_maybe_auto_run_fo_check_uses_initial_status_and_runs_for_each_trade() -> None:
    db = _mock_db_with_trigger("auto")
    trades = [SimpleNamespace(trade_id="TRD-006"), SimpleNamespace(trade_id="TRD-007")]

    with (
        patch("src.infrastructure.seed.TradeRepository") as repo_cls,
        patch("src.infrastructure.rule_engine.run_fo_check") as run_fo_check,
    ):
        repo_cls.return_value.list.return_value = (trades, len(trades))

        _maybe_auto_run_fo_check(db)

        repo_cls.return_value.list.assert_called_once_with(
            workflow_status="Initial",
            limit=100,
            offset=0,
        )
        run_fo_check.assert_any_call("TRD-006", db)
        run_fo_check.assert_any_call("TRD-007", db)
        assert run_fo_check.call_count == 2


def test_maybe_auto_run_fo_check_skips_when_trigger_is_manual() -> None:
    db = _mock_db_with_trigger("manual")

    with (
        patch("src.infrastructure.seed.TradeRepository") as repo_cls,
        patch("src.infrastructure.rule_engine.run_fo_check") as run_fo_check,
    ):
        _maybe_auto_run_fo_check(db)

        repo_cls.assert_not_called()
        run_fo_check.assert_not_called()
