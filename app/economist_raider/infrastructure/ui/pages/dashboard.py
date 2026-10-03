"""Main dashboard page."""

import asyncio
from typing import Callable

from nicegui import ui

from economist_raider.application.use_cases.get_current_indicators import GetCurrentIndicators
from economist_raider.domain.entities.indicator import Indicator
from economist_raider.domain.ports.indicator_repository import IndicatorRepository
from economist_raider.domain.ports.source_repository import SourceRepository
from economist_raider.infrastructure.ui.components.indicator_card import indicator_card


def create_dashboard(
    indicator_repo: IndicatorRepository,
    source_repo: SourceRepository,
    collect_fn: Callable | None = None,
) -> None:
    """Register the dashboard page with NiceGUI."""

    @ui.page("/")
    def dashboard() -> None:
        use_case = GetCurrentIndicators(indicator_repo)
        indicators = use_case.execute()

        # Header
        with ui.header().classes("bg-blue-900 text-white px-6 py-4"):
            with ui.row().classes("items-center gap-4 w-full"):
                ui.icon("bar_chart", size="2rem")
                ui.label("Observatorio Económico — Colombia").classes(
                    "text-2xl font-bold"
                )
                ui.space()
                if collect_fn:
                    collect_btn = ui.button(
                        "Recolectar datos",
                        icon="cloud_download",
                        on_click=lambda: _run_collect(collect_fn, collect_btn),
                    ).props("flat").classes("text-white")
                ui.button(
                    "Recargar",
                    icon="refresh",
                    on_click=lambda: ui.navigate.reload(),
                ).props("flat").classes("text-white")

        with ui.column().classes("w-full max-w-7xl mx-auto px-6 py-8 gap-8"):

            if not indicators:
                _empty_state()
                return

            # Indicators grid
            ui.label("Indicadores Actuales").classes("text-xl font-semibold text-grey-8")

            with ui.row().classes("flex-wrap gap-4"):
                for ind in indicators:
                    indicator_card(
                        ind,
                        on_click=lambda i=ind: _show_history_dialog(i, indicator_repo),
                        on_source_click=lambda i=ind: _show_source_dialog(i, source_repo),
                    )

            # Status footer
            _collection_status_section(source_repo)


def _empty_state() -> None:
    with ui.column().classes("items-center justify-center py-24 gap-4 w-full"):
        ui.icon("cloud_download", size="4rem").classes("text-grey-4")
        ui.label("No hay datos disponibles").classes("text-xl text-grey-6")
        ui.label(
            "Ejecuta la primera recolección con: python main.py --collect"
        ).classes("text-sm text-grey-5 font-mono")


def _show_history_dialog(indicator: Indicator, indicator_repo: IndicatorRepository) -> None:
    from economist_raider.infrastructure.ui.components.history_chart import history_dialog
    history_dialog(indicator, indicator_repo)


def _show_source_dialog(indicator: Indicator, source_repo: SourceRepository) -> None:
    from economist_raider.infrastructure.ui.components.source_detail import source_detail_dialog
    source_detail_dialog(indicator.source_id, source_repo)


def _collection_status_section(source_repo: SourceRepository) -> None:
    from economist_raider.infrastructure.ui.components.collection_status import collection_status_panel
    ui.separator()
    ui.label("Estado del Observatorio").classes("text-lg font-semibold text-grey-7 mt-4")
    collection_status_panel(source_repo)


async def _run_collect(collect_fn: Callable, btn: ui.button) -> None:
    """Run collection in a background thread so the UI stays responsive."""
    btn.props("loading disable")
    btn.text = "Recolectando..."
    try:
        await asyncio.to_thread(collect_fn)
        ui.notify("Recolección completada", type="positive", position="top-right")
        await asyncio.sleep(0.5)
        ui.navigate.reload()
    except Exception as exc:
        ui.notify(f"Error: {exc}", type="negative", position="top-right", timeout=8000)
        btn.props(remove="loading disable")
        btn.text = "Recolectar datos"
