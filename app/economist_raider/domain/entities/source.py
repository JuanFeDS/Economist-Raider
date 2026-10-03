"""Source domain entity."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    OFFICIAL_GOV = "OFFICIAL_GOV"
    CENTRAL_BANK = "CENTRAL_BANK"
    MEDIA = "MEDIA"


class RunStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RUNNING = "RUNNING"
    NEVER = "NEVER"


class Source(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    source_type: SourceType
    base_url: str
    last_successful_run: datetime | None = None
    last_run_at: datetime | None = None
    last_run_status: RunStatus = RunStatus.NEVER
    last_error: str | None = None
    update_frequency: str
    is_active: bool = True

    model_config = {"frozen": True}
