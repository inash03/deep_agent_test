"""Fitness function: the rules dashboard must stay in sync with the engine.

Promoted from an independent `spec-reviewer` finding (see ADR-0009 /
docs/governance/automated-gates.md): a new engine rule was added to
``src.domain.check_rules.FO_RULES`` but not to the hand-written ``_FO_RULES``
registry that powers ``GET /api/v1/rules`` (FR-10), so it was invisible to
operators. The OpenAPI drift test cannot catch this — the gap is in response
*data*, not schema. This test makes that class of defect a machine check, so no
human/AI review is needed for it again.

Direction enforced here: every engine rule must appear in the dashboard with a
matching severity. The reverse direction (dashboard entries with no engine rule,
e.g. the planned ``value_date_business_calendar``) is a separate product
decision and is intentionally not gated yet.
"""

from src.domain.check_rules import BO_RULES, FO_RULES
from src.presentation.routers.rules import _BO_RULES, _FO_RULES


def _dashboard_severity_by_name(dashboard) -> dict[str, str]:
    return {r.rule_name: r.severity for r in dashboard}


def test_every_fo_engine_rule_is_on_the_dashboard() -> None:
    dashboard = _dashboard_severity_by_name(_FO_RULES)
    missing = [r.rule_name for r in FO_RULES if r.rule_name not in dashboard]
    assert not missing, f"FO rules missing from GET /api/v1/rules dashboard: {missing}"


def test_every_bo_engine_rule_is_on_the_dashboard() -> None:
    dashboard = _dashboard_severity_by_name(_BO_RULES)
    missing = [r.rule_name for r in BO_RULES if r.rule_name not in dashboard]
    assert not missing, f"BO rules missing from GET /api/v1/rules dashboard: {missing}"


def test_dashboard_severities_match_the_engine() -> None:
    fo = _dashboard_severity_by_name(_FO_RULES)
    bo = _dashboard_severity_by_name(_BO_RULES)
    mismatches = [
        (r.rule_name, r.severity, fo[r.rule_name])
        for r in FO_RULES
        if r.rule_name in fo and fo[r.rule_name] != r.severity
    ] + [
        (r.rule_name, r.severity, bo[r.rule_name])
        for r in BO_RULES
        if r.rule_name in bo and bo[r.rule_name] != r.severity
    ]
    assert not mismatches, f"severity drift (rule, engine, dashboard): {mismatches}"
