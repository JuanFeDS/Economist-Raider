"""NiceGUI CollectionStatus component — observatory health panel."""

from nicegui import ui

from economist_raider.application.use_cases.get_collection_status import (
    GetCollectionStatus,
    SourceStatus,
)
from economist_raider.domain.entities.source import RunStatus
from economist_raider.domain.ports.source_repository import SourceRepository

_STATUS_ICON = {
    RunStatus.SUCCESS: ("check_circle", "text-green-6"),
    RunStatus.FAILED: ("error", "text-red-6"),
    RunStatus.RUNNING: ("sync", "text-orange-6"),
    RunStatus.NEVER: ("radio_button_unchecked", "text-grey-5"),
}

_STATUS_LABEL = {
    RunStatus.SUCCESS: "OK",
    RunStatus.FAILED: "Error",
    RunStatus.RUNNING: "Ejecutando",
    RunStatus.NEVER: "Sin datos",
}


def collection_status_panel(source_repo: SourceRepository) -> None:
    """Render the collection status table for all active sources."""
    use_case = GetCollectionStatus(source_repo)
    statuses = use_case.execute()

    if not statuses:
        ui.label("No hay fuentes activas registradas.").classes(
            "text-sm text-grey-5"
        )
        return

    with ui.row().classes("flex-wrap gap-4 w-full"):
        for status in statuses:
            _source_status_chip(status)


def _source_status_chip(status: SourceStatus) -> None:
    icon_name, icon_class = _STATUS_ICON.get(
        status.last_run_status, ("help_outline", "text-grey-5")
    )
    label = _STATUS_LABEL.get(status.last_run_status, "—")

    with ui.card().classes("px-4 py-3 min-w-48"):
        with ui.row().classes("items-center gap-2"):
            ui.icon(icon_name, size="1.2rem").classes(icon_class)
            ui.label(status.name).classes("text-sm font-medium")

        ts = status.last_successful_run
        ui.label(
            f"Última OK: {ts.strftime('%d/%m %H:%M') if ts else 'Nunca'}"
        ).classes("text-xs text-grey-6 mt-1")

        ui.label(
            f"Frecuencia: {status.update_frequency}"
        ).classes("text-xs text-grey-5")

        if status.last_run_status == RunStatus.FAILED and status.last_error:
            ui.tooltip(status.last_error).classes("text-xs max-w-xs")
