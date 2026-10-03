"""NiceGUI SourceDetail component — shows source attribution."""

from uuid import UUID

from nicegui import ui

from economist_raider.domain.entities.source import RunStatus, SourceType
from economist_raider.domain.ports.source_repository import SourceRepository

_SOURCE_TYPE_LABELS = {
    SourceType.OFFICIAL_GOV: "Gobierno oficial",
    SourceType.CENTRAL_BANK: "Banco central",
    SourceType.MEDIA: "Medios públicos",
}

_STATUS_COLORS = {
    RunStatus.SUCCESS: "positive",
    RunStatus.FAILED: "negative",
    RunStatus.RUNNING: "warning",
    RunStatus.NEVER: "grey",
}

_STATUS_LABELS = {
    RunStatus.SUCCESS: "Exitoso",
    RunStatus.FAILED: "Fallido",
    RunStatus.RUNNING: "Ejecutando",
    RunStatus.NEVER: "Sin ejecuciones",
}


def source_detail_dialog(source_id: UUID, source_repo: SourceRepository) -> None:
    """Open a dialog with source attribution details."""
    source = source_repo.get_by_id(source_id)

    with ui.dialog() as dialog, ui.card().classes("w-96"):
        with ui.row().classes("items-center justify-between w-full"):
            ui.label("Fuente de datos").classes("text-lg font-bold")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense")

        if source is None:
            ui.label("Fuente no encontrada").classes("text-grey-6 text-sm")
            dialog.open()
            return

        ui.separator()

        with ui.column().classes("gap-3 w-full"):
            # Source name + type
            with ui.row().classes("items-center gap-2"):
                ui.icon("account_balance", size="1.5rem").classes("text-blue-7")
                ui.label(source.name).classes("text-base font-semibold")

            ui.badge(
                _SOURCE_TYPE_LABELS.get(source.source_type, source.source_type.value),
                color="blue",
            ).classes("text-xs self-start")

            # URL
            with ui.row().classes("items-center gap-2"):
                ui.icon("link", size="1rem").classes("text-grey-6")
                ui.link(source.base_url, target=source.base_url).classes(
                    "text-sm text-blue-600 break-all"
                )

            ui.separator()

            # Run status
            status_color = _STATUS_COLORS.get(source.last_run_status, "grey")
            status_label = _STATUS_LABELS.get(source.last_run_status, "—")

            with ui.row().classes("items-center gap-2"):
                ui.label("Estado:").classes("text-sm text-grey-7 font-medium")
                ui.badge(status_label, color=status_color).classes("text-xs")

            # Last successful run
            with ui.row().classes("items-center gap-2"):
                ui.label("Última exitosa:").classes("text-sm text-grey-7 font-medium")
                ts = source.last_successful_run
                ui.label(
                    ts.strftime("%d/%m/%Y %H:%M") if ts else "Nunca"
                ).classes("text-sm")

            # Frequency
            with ui.row().classes("items-center gap-2"):
                ui.label("Frecuencia:").classes("text-sm text-grey-7 font-medium")
                ui.label(source.update_frequency.capitalize()).classes("text-sm")

            # Error (if any)
            if source.last_error:
                with ui.expansion("Ver error", icon="error").classes("w-full text-red-6"):
                    ui.label(source.last_error).classes("text-xs font-mono text-red-7 break-all")

    dialog.open()
