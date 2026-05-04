"""Trade classification helpers."""

from __future__ import annotations

from datetime import date, timedelta


def count_business_days_exclusive_start(start: date, end: date) -> int:
    """Count Mon-Fri days from the day after start through end."""
    if end <= start:
        return 0

    current = start + timedelta(days=1)
    count = 0
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def calculate_trade_type(trade_date: date, value_date: date) -> str:
    """Classify as Forward when value date is more than 2 business days out."""
    business_days = count_business_days_exclusive_start(trade_date, value_date)
    return "Forward" if business_days > 2 else "Spot"
