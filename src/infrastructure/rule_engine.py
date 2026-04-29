"""Rule engine — orchestrates FoCheck and BoCheck execution.

Fetches required master data from the DB, runs domain-layer rules,
persists check results to the trade record, and advances workflow_status.

Workflow transitions:
  FoCheck: any ERROR failure  → FoAgentToCheck
           only WARNINGs / all pass → FoValidated
  BoCheck: any failure        → BoAgentToCheck
           all pass           → BoValidated
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from src.domain.check_rules import BO_RULES, FO_RULES
from src.domain.entities import CheckResult
from src.infrastructure.db.app_setting_repository import AppSettingRepository
from src.infrastructure.db.models import CounterpartyModel, SettlementInstructionModel
from src.infrastructure.bo_triage_use_case import BoTriageUseCase
from src.infrastructure.fo_triage_use_case import FoTriageUseCase
from src.infrastructure.db.trade_repository import TradeRepository

_logger = logging.getLogger("stp_triage.rule_engine")
_fo_triage_use_case: FoTriageUseCase | None = None
_bo_triage_use_case: BoTriageUseCase | None = None


def _build_error_context(results: list[CheckResult]) -> str:
    failed = [r for r in results if not r.passed]
    if not failed:
        return ""
    return "\n".join(f"[{r.rule_name}] {r.message}" for r in failed)


def _get_fo_triage_use_case() -> FoTriageUseCase:
    global _fo_triage_use_case
    if _fo_triage_use_case is None:
        _fo_triage_use_case = FoTriageUseCase()
    return _fo_triage_use_case


def _get_bo_triage_use_case() -> BoTriageUseCase:
    global _bo_triage_use_case
    if _bo_triage_use_case is None:
        _bo_triage_use_case = BoTriageUseCase()
    return _bo_triage_use_case


# ---------------------------------------------------------------------------
# FoCheck
# ---------------------------------------------------------------------------


def run_fo_check(trade_id: str, db: Session) -> tuple[list[CheckResult], str]:
    """Run FoCheck rules on the current version of a trade.

    Returns (results, new_workflow_status).
    Commits the updated workflow_status and fo_check_results to DB.
    """
    repo = TradeRepository(db)
    trade = repo.get_current(trade_id)
    if trade is None:
        raise ValueError(f"Trade '{trade_id}' not found")

    results: list[CheckResult] = []
    for rule in FO_RULES:
        passed, message = rule.check_fn(trade)
        results.append(
            CheckResult(
                rule_name=rule.rule_name,
                passed=passed,
                severity=rule.severity,
                message=message,
            )
        )
        _logger.debug(
            "fo_check rule executed",
            extra={"trade_id": trade_id, "rule": rule.rule_name, "passed": passed},
        )

    # Only ERROR-severity failures trigger FoAgentToCheck
    has_errors = any(
        not r.passed
        for r, rule in zip(results, FO_RULES)
        if rule.severity == "error"
    )
    new_status = "FoAgentToCheck" if has_errors else "FoValidated"

    repo.update_workflow_status(
        trade_id,
        new_status,
        fo_check_results=[r.model_dump() for r in results],
    )
    db.commit()

    _logger.info(
        "fo_check completed",
        extra={
            "trade_id": trade_id,
            "new_status": new_status,
            "total": len(results),
            "failures": sum(1 for r in results if not r.passed),
        },
    )
    if new_status == "FoAgentToCheck":
        setting = AppSettingRepository(db).get("fo_triage_trigger")
        if setting and setting.value == "auto":
            try:
                _get_fo_triage_use_case().start(
                    trade_id=trade_id,
                    error_context=_build_error_context(results),
                )
                _logger.info("fo_triage auto-triggered", extra={"trade_id": trade_id})
            except Exception as exc:  # noqa: BLE001
                _logger.warning(
                    "fo_triage auto-trigger failed",
                    extra={"trade_id": trade_id, "error": str(exc)},
                )
    return results, new_status


# ---------------------------------------------------------------------------
# BoCheck
# ---------------------------------------------------------------------------


def run_bo_check(trade_id: str, db: Session) -> tuple[list[CheckResult], str]:
    """Run BoCheck rules on the current version of a trade.

    Returns (results, new_workflow_status).
    Commits the updated workflow_status and bo_check_results to DB.
    """
    repo = TradeRepository(db)
    trade = repo.get_current(trade_id)
    if trade is None:
        raise ValueError(f"Trade '{trade_id}' not found")

    # Pre-fetch master data required by BO rules
    cp = (
        db.query(CounterpartyModel)
        .filter(CounterpartyModel.lei == trade.counterparty_lei)
        .first()
    )
    ssi = (
        db.query(SettlementInstructionModel)
        .filter(
            SettlementInstructionModel.lei == trade.counterparty_lei,
            SettlementInstructionModel.currency == trade.currency,
            SettlementInstructionModel.is_external.is_(False),
        )
        .first()
    )

    results: list[CheckResult] = []
    for rule in BO_RULES:
        passed, message = rule.check_fn(trade, cp, ssi)
        results.append(
            CheckResult(
                rule_name=rule.rule_name,
                passed=passed,
                severity=rule.severity,
                message=message,
            )
        )
        _logger.debug(
            "bo_check rule executed",
            extra={"trade_id": trade_id, "rule": rule.rule_name, "passed": passed},
        )

    has_errors = any(not r.passed for r in results)
    new_status = "BoAgentToCheck" if has_errors else "BoValidated"

    repo.update_workflow_status(
        trade_id,
        new_status,
        bo_check_results=[r.model_dump() for r in results],
    )
    db.commit()

    _logger.info(
        "bo_check completed",
        extra={
            "trade_id": trade_id,
            "new_status": new_status,
            "total": len(results),
            "failures": sum(1 for r in results if not r.passed),
        },
    )
    if new_status == "BoAgentToCheck":
        setting = AppSettingRepository(db).get("bo_triage_trigger")
        if setting and setting.value == "auto":
            try:
                _get_bo_triage_use_case().start(
                    trade_id=trade_id,
                    error_context=_build_error_context(results),
                )
                _logger.info("bo_triage auto-triggered", extra={"trade_id": trade_id})
            except Exception as exc:  # noqa: BLE001
                _logger.warning(
                    "bo_triage auto-trigger failed",
                    extra={"trade_id": trade_id, "error": str(exc)},
                )
    return results, new_status


# ---------------------------------------------------------------------------
# Auto-trigger helpers
# ---------------------------------------------------------------------------


def maybe_run_fo_check(trade_id: str, db: Session) -> tuple[list[CheckResult], str] | None:
    """Trigger the FoCheck workflow for a trade.

    - auto mode: run rules immediately → FoAgentToCheck or FoValidated.
      When FoValidated, also chains into maybe_run_bo_check automatically.
    - manual mode: set status to FoCheck (awaiting user-triggered run).

    Returns (results, new_status) when auto ran, None when manual.
    """
    setting = AppSettingRepository(db).get("fo_check_trigger")
    if setting and setting.value == "auto":
        results, new_status = run_fo_check(trade_id, db)
        if new_status == "FoValidated":
            maybe_run_bo_check(trade_id, db)
        return results, new_status
    TradeRepository(db).update_workflow_status(trade_id, "FoCheck")
    db.commit()
    return None


def maybe_run_bo_check(trade_id: str, db: Session) -> tuple[list[CheckResult], str] | None:
    """Trigger the BoCheck workflow for a trade.

    - auto mode: run rules immediately → BoAgentToCheck or BoValidated.
    - manual mode: set status to BoCheck (awaiting user-triggered run).

    Returns (results, new_status) when auto ran, None when manual.
    """
    setting = AppSettingRepository(db).get("bo_check_trigger")
    if setting and setting.value == "auto":
        return run_bo_check(trade_id, db)
    TradeRepository(db).update_workflow_status(trade_id, "BoCheck")
    db.commit()
    return None
