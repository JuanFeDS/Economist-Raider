"""Abstract port for source persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from economist_raider.domain.entities.collection_run import CollectionRun
from economist_raider.domain.entities.source import RunStatus, Source


class SourceRepository(ABC):

    @abstractmethod
    def get_all_active(self) -> list[Source]:
        """Return all active sources for the scheduler."""

    @abstractmethod
    def get_by_id(self, source_id: UUID) -> Source | None:
        """Return a source by its UUID."""

    @abstractmethod
    def update_run_status(
        self,
        source_id: UUID,
        status: RunStatus,
        error: str | None = None,
    ) -> None:
        """Update last run status and timestamp for a source."""

    @abstractmethod
    def save_collection_run(self, run: CollectionRun) -> None:
        """Record the result of a collection execution."""

    @abstractmethod
    def upsert(self, source: Source) -> None:
        """Insert the source if it doesn't exist yet (no-op if already present)."""
