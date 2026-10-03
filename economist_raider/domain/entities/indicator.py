"""Indicator domain entity."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class IndicatorCategory(StrEnum):
    MACROECONOMIC = "MACROECONOMIC"
    MONETARY = "MONETARY"
    LABOR = "LABOR"
    FISCAL = "FISCAL"


class PeriodType(StrEnum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"


class Indicator(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    category: IndicatorCategory
    value: Decimal
    unit: str
    measured_at: date
    period_type: PeriodType
    change_absolute: Decimal | None = None
    change_pct: Decimal | None = None
    source_id: UUID
    is_quarantined: bool = False
    quarantine_reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_invariants(self) -> "Indicator":
        if self.measured_at > date.today():
            raise ValueError("measured_at cannot be in the future")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        return self
