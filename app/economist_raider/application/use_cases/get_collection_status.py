"""Use case: retrieve the collection status for all active sources."""

from dataclasses import dataclass
from datetime import datetime

from economist_raider.domain.entities.source import RunStatus, Source
from economist_raider.domain.ports.source_repository import SourceRepository


@dataclass(frozen=True)
class SourceStatus:
    source_id: str
    name: str
    last_run_status: RunStatus
    last_run_at: datetime | None
    last_successful_run: datetime | None
    last_error: str | None
    update_frequency: str


class GetCollectionStatus:
    def __init__(self, source_repo: SourceRepository) -> None:
        self._repo = source_repo

    def execute(self) -> list[SourceStatus]:
        """Return status summary for all active sources."""
        sources = self._repo.get_all_active()
        return [_to_status(s) for s in sources]


def _to_status(source: Source) -> SourceStatus:
    return SourceStatus(
        source_id=str(source.id),
        name=source.name,
        last_run_status=source.last_run_status,
        last_run_at=source.last_run_at,
        last_successful_run=source.last_successful_run,
        last_error=source.last_error,
        update_frequency=source.update_frequency,
    )
