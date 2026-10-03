"""Abstract port for indicator persistence."""

from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from economist_raider.domain.entities.historical_series import Measurement
from economist_raider.domain.entities.indicator import Indicator


class IndicatorRepository(ABC):

    @abstractmethod
    def get_latest(self, indicator_name: str) -> Indicator | None:
        """Return the most recent indicator for a given name."""

    @abstractmethod
    def get_all_latest(self) -> list[Indicator]:
        """Return the latest value for each active indicator."""

    @abstractmethod
    def save(self, indicator: Indicator) -> None:
        """Persist an indicator. Skips silently on duplicate (name + date)."""

    @abstractmethod
    def get_history(
        self,
        indicator_name: str,
        from_date: date,
        to_date: date,
    ) -> list[Measurement]:
        """Return historical measurements in the given date range."""

    @abstractmethod
    def exists(self, indicator_name: str, measured_at: date) -> bool:
        """Check if a measurement already exists to prevent duplicates."""
