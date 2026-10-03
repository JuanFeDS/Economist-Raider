"""Dashboard presenter — formats domain objects for display."""

from datetime import date, datetime
from decimal import Decimal

_MONTHS_ES = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr",
    5: "may", 6: "jun", 7: "jul", 8: "ago",
    9: "sep", 10: "oct", 11: "nov", 12: "dic",
}


def format_value(value: Decimal, unit: str) -> str:
    """Format a Decimal value with thousands separator and unit."""
    try:
        f = float(value)
        if f >= 1_000:
            formatted = f"{f:,.2f}"
        else:
            formatted = f"{f:.2f}"
        return f"{formatted} {unit}".strip()
    except (ValueError, TypeError):
        return f"{value} {unit}".strip()


def format_change(change_pct: Decimal | None, change_absolute: Decimal | None) -> str:
    """Format the change values with sign and color hint."""
    if change_pct is None:
        return "—"
    sign = "▲" if change_pct >= 0 else "▼"
    pct_str = f"{abs(float(change_pct)):.2f}%"
    if change_absolute is not None:
        abs_str = f"{float(change_absolute):+.2f}"
        return f"{sign} {abs_str} ({pct_str})"
    return f"{sign} {pct_str}"


def change_color(change_pct: Decimal | None) -> str:
    """Return 'positive', 'negative', or 'neutral' for CSS class selection."""
    if change_pct is None:
        return "neutral"
    return "positive" if change_pct >= 0 else "negative"


def format_date_es(d: date) -> str:
    """Format a date in Spanish: '12 abr 2026'."""
    return f"{d.day} {_MONTHS_ES[d.month]} {d.year}"


def format_datetime_es(dt: datetime | None) -> str:
    """Format a datetime in Spanish: '12 abr 2026 14:35'."""
    if dt is None:
        return "Nunca"
    return f"{format_date_es(dt.date())} {dt.strftime('%H:%M')}"
