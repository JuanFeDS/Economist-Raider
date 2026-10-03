"""Measurement entity for historical time series."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Measurement(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    indicator_name: str
    value: Decimal
    unit: str
    measured_at: date
    source_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}
