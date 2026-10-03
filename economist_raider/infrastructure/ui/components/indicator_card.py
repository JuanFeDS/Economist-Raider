"""NiceGUI IndicatorCard component."""

from decimal import Decimal
from typing import Callable

from nicegui import ui

from economist_raider.domain.entities.indicator import Indicator, IndicatorCategory

CATEGORY_COLORS: dict[IndicatorCategory, str] = {
    IndicatorCategory.MACROECONOMIC: "blue",
    IndicatorCategory.MONETARY: "purple",
    IndicatorCategory.LABOR: "orange",
    IndicatorCategory.FISCAL: "green",
}

CATEGORY_LABELS: dict[IndicatorCategory, str] = {
    IndicatorCategory.MACROECONOMIC: "Macroeconómico",
    IndicatorCategory.MONETARY: "Monetario",
    IndicatorCategory.LABOR: "Laboral",
    IndicatorCategory.FISCAL: "Fiscal",
}


def indicator_card(
    indicator: Indicator,
    on_click: Callable[[Indicator], None] | None = None,
    on_source_click: Callable[[Indicator], None] | None = None,
) -> None:
    """Render a single indicator card."""
    color = CATEGORY_COLORS.get(indicator.category, "grey")
    change_color = _change_color(indicator.change_pct)

    with ui.card().classes("w-64 cursor-pointer hover:shadow-lg transition-shadow").on(
        "click", lambda: on_click(indicator) if on_click else None
    ):
        # Category badge
        with ui.row().classes("items-center justify-between w-full"):
            ui.badge(
                CATEGORY_LABELS.get(indicator.category, indicator.category.value),
                color=color,
            ).classes("text-xs")
            if on_source_click:
                ui.button(
                    icon="info",
                    on_click=lambda: on_source_click(indicator),
                ).props("flat round dense size=sm").classes("text-grey-6")

        # Indicator name
        ui.label(indicator.name).classes("text-lg font-bold mt-2")

        # Value + unit
        ui.label(
            f"{_fmt_value(indicator.value)} {indicator.unit}"
        ).classes("text-3xl font-mono font-semibold mt-1")

        # Change
        if indicator.change_pct is not None:
            sign = "▲" if indicator.change_pct >= 0 else "▼"
            ui.label(
                f"{sign} {abs(indicator.change_pct):.2f}%"
            ).classes(f"text-sm font-medium text-{change_color}-600 mt-1")

        # Date
        ui.label(
            f"Fecha: {indicator.measured_at.strftime('%d/%m/%Y')}"
        ).classes("text-xs text-grey-6 mt-2")


def _fmt_value(value: Decimal) -> str:
    """Format Decimal for display: no trailing zeros, thousands separator."""
    try:
        f = float(value)
        if f >= 1000:
            return f"{f:,.2f}"
        return f"{f:.2f}"
    except Exception:
        return str(value)


def _change_color(change_pct: Decimal | None) -> str:
    if change_pct is None:
        return "grey"
    return "green" if change_pct >= 0 else "red"
