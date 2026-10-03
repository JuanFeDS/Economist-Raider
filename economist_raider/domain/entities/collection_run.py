"""CollectionRun entity — records each scraping execution."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from economist_raider.domain.entities.source import RunStatus


class CollectionRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    status: RunStatus = RunStatus.RUNNING
    records_collected: int = 0
    records_quarantined: int = 0
    error_message: str | None = None

    model_config = {"frozen": False}

    def complete(self, records_collected: int, records_quarantined: int = 0) -> None:
        self.finished_at = datetime.utcnow()
        self.status = RunStatus.SUCCESS
        self.records_collected = records_collected
        self.records_quarantined = records_quarantined

    def fail(self, error: str) -> None:
        self.finished_at = datetime.utcnow()
        self.status = RunStatus.FAILED
        self.error_message = error
