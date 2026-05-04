from datetime import date

from src.domain.trade_classification import (
    calculate_trade_type,
    count_business_days_exclusive_start,
)


def test_same_day_or_invalid_value_date_is_spot() -> None:
    assert calculate_trade_type(date(2026, 4, 1), date(2026, 4, 1)) == "Spot"
    assert calculate_trade_type(date(2026, 4, 2), date(2026, 4, 1)) == "Spot"


def test_two_business_days_or_less_is_spot() -> None:
    assert count_business_days_exclusive_start(date(2026, 4, 1), date(2026, 4, 3)) == 2
    assert calculate_trade_type(date(2026, 4, 1), date(2026, 4, 3)) == "Spot"


def test_weekends_are_excluded_from_business_day_count() -> None:
    assert count_business_days_exclusive_start(date(2026, 4, 3), date(2026, 4, 7)) == 2
    assert calculate_trade_type(date(2026, 4, 3), date(2026, 4, 7)) == "Spot"


def test_more_than_two_business_days_is_forward() -> None:
    assert count_business_days_exclusive_start(date(2026, 4, 1), date(2026, 4, 6)) == 3
    assert calculate_trade_type(date(2026, 4, 1), date(2026, 4, 6)) == "Forward"
