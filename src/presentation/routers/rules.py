"""Rule list endpoint — returns FO and BO rule definitions."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


class RuleOut(BaseModel):
    rule_name: str
    severity: str
    check_type: str
    description: str
    is_stub: bool


class RuleListResponse(BaseModel):
    fo_rules: list[RuleOut]
    bo_rules: list[RuleOut]


_FO_RULES: list[RuleOut] = [
    RuleOut(
        rule_name="trade_date_not_future",
        severity="error",
        check_type="FO",
        description="取引日が本日以降の未来日でないことを確認する。未来日の取引は入力ミスの可能性がある。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="trade_date_not_weekend",
        severity="error",
        check_type="FO",
        description="取引日が土曜・日曜でないことを確認する。FX市場は営業日のみ取引可能。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="value_date_after_trade_date",
        severity="error",
        check_type="FO",
        description="決済日（Value Date）が取引日より後の日付であることを確認する。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="value_date_not_past",
        severity="error",
        check_type="FO",
        description="決済日が本日より過去でないことを確認する。過去の決済日は即時決済不可。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="value_date_settlement_cycle",
        severity="warning",
        check_type="FO",
        description="決済日が取引日のT+2（営業日2日後）以降であることを確認する。FX標準決済サイクル（SWIFT基準）への準拠チェック。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="amount_positive",
        severity="error",
        check_type="FO",
        description="取引金額がゼロより大きいことを確認する。ゼロ以下の金額は無効取引。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="settlement_currency_consistency",
        severity="error",
        check_type="FO",
        description="決済通貨が取引商品ID（例: EURUSD）に含まれていることを確認する。通貨ペアと決済通貨の整合性チェック。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="counterparty_exists",
        severity="error",
        check_type="FO",
        description="カウンターパーティ存在確認（スタブ）。実際のチェックは BoCheck の counterparty_exists で実施。",
        is_stub=True,
    ),
    RuleOut(
        rule_name="instrument_exists",
        severity="error",
        check_type="FO",
        description="金融商品存在確認（スタブ）。実際のチェックは BoCheck で実施。",
        is_stub=True,
    ),
]

_BO_RULES: list[RuleOut] = [
    RuleOut(
        rule_name="counterparty_exists",
        severity="error",
        check_type="BO",
        description="カウンターパーティのLEI（法人識別子）がマスタデータに登録されていることを確認する。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="counterparty_active",
        severity="error",
        check_type="BO",
        description="カウンターパーティが現在アクティブ状態であることを確認する。非アクティブのカウンターパーティとの取引は不可（SWIFT AG01相当）。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="ssi_exists",
        severity="error",
        check_type="BO",
        description="対象LEIと通貨の組み合わせに対して内部SSI（決済指示）が登録されていることを確認する。SSI未登録は決済不可（SWIFT AC01相当）。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="bic_format_valid",
        severity="error",
        check_type="BO",
        description="SSIに登録されたBICコードが8文字または11文字であることを確認する（SWIFT標準）。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="iban_format_valid",
        severity="error",
        check_type="BO",
        description="SSIのIBANが国際標準フォーマット [A-Z]{2}[0-9]{2}[A-Z0-9]{1,30} に準拠していることを確認する（SWIFT BE01相当）。",
        is_stub=False,
    ),
    RuleOut(
        rule_name="risk_limit_check",
        severity="error",
        check_type="BO",
        description="取引金額がカウンターパーティのリスク限度額内であることを確認する（スタブ — 常にパス）。",
        is_stub=True,
    ),
    RuleOut(
        rule_name="compliance_check",
        severity="error",
        check_type="BO",
        description="カウンターパーティが制裁リスト・コンプライアンス要件を満たすことを確認する（スタブ — 常にパス）。",
        is_stub=True,
    ),
    RuleOut(
        rule_name="settlement_confirmed",
        severity="error",
        check_type="BO",
        description="SWIFTによる決済確認を受け取ったことを確認する（スタブ）。AC01/AM04/SLA超過などのSWIFTリジェクトシナリオをプリシードデータで再現可能。",
        is_stub=True,
    ),
]


@router.get("", response_model=RuleListResponse)
def list_rules() -> RuleListResponse:
    return RuleListResponse(fo_rules=_FO_RULES, bo_rules=_BO_RULES)
