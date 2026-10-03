"""NiceGUI HistoryChart component with time-range selector."""

from datetime import date, timedelta

from nicegui import ui

from economist_raider.domain.entities.indicator import Indicator
from economist_raider.domain.ports.indicator_repository import IndicatorRepository

_RANGES = {
    "3m": 90,
    "6m": 180,
    "12m": 365,
}


def history_dialog(indicator: Indicator, indicator_repo: IndicatorRepository) -> None:
    """Open a dialog with the historical chart for *indicator*."""
    with ui.dialog().props("maximized") as dialog, ui.card().classes(
        "w-full max-w-4xl mx-auto my-8"
    ):
        with ui.row().classes("items-center justify-between w-full px-4 pt-4"):
            ui.label(f"Tendencia histórica — {indicator.name}").classes(
                "text-xl font-bold"
            )
            ui.button(icon="close", on_click=dialog.close).props("flat round dense")

        # Time range selector
        selected_range: dict = {"days": 180}

        with ui.row().classes("gap-2 px-4"):
            for label, days in _RANGES.items():
                ui.button(
                    label.upper(),
                    on_click=lambda d=days: _refresh_chart(
                        chart_container, indicator, indicator_repo, d, selected_range
                    ),
                ).props("outline").classes("text-sm")

        # Chart container
        chart_container = ui.column().classes("w-full px-4 pb-4")
        _refresh_chart(
            chart_container, indicator, indicator_repo,
            selected_range["days"], selected_range
        )

    dialog.open()


def _refresh_chart(
    container: ui.column,
    indicator: Indicator,
    indicator_repo: IndicatorRepository,
    days: int,
    selected_range: dict,
) -> None:
    """Reload chart data for the given time range."""
    selected_range["days"] = days
    container.clear()

    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    measurements = indicator_repo.get_history(indicator.name, from_date, to_date)

    with container:
        if not measurements:
            with ui.column().classes("items-center py-12 gap-2 w-full"):
                ui.icon("show_chart", size="3rem").classes("text-grey-4")
                ui.label("Sin datos históricos para este rango").classes(
                    "text-grey-6"
                )
            return

        x_data = [m.measured_at.isoformat() for m in measurements]
        y_data = [float(m.value) for m in measurements]

        ui.echart(
            {
                "tooltip": {
                    "trigger": "axis",
                    "formatter": "{b}<br/>{a}: {c}",
                },
                "xAxis": {
                    "type": "time",
                    "data": x_data,
                    "axisLabel": {"formatter": "{MM}/{dd}/{yyyy}"},
                },
                "yAxis": {
                    "type": "value",
                    "name": indicator.unit,
                    "nameLocation": "end",
                },
                "series": [
                    {
                        "name": indicator.name,
                        "type": "line",
                        "data": list(zip(x_data, y_data)),
                        "smooth": True,
                        "symbol": "circle",
                        "symbolSize": 4,
                        "lineStyle": {"width": 2},
                    }
                ],
                "grid": {"containLabel": True},
            }
        ).classes("w-full h-96")

        ui.label(
            f"{len(measurements)} mediciones · "
            f"{measurements[0].measured_at.strftime('%d/%m/%Y')} – "
            f"{measurements[-1].measured_at.strftime('%d/%m/%Y')}"
        ).classes("text-xs text-grey-5 text-right w-full mt-1")
