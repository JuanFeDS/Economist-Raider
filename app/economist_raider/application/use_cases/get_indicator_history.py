"""Use case: retrieve historical measurements for a single indicator."""

from datetime import date

from economist_raider.domain.entities.historical_series import Measurement
from economist_raider.domain.ports.indicator_repository import IndicatorRepository


class GetIndicatorHistory:
    def __init__(self, indicator_repo: IndicatorRepository) -> None:
        self._repo = indicator_repo

    def execute(
        self,
        indicator_name: str,
        from_date: date,
        to_date: date,
    ) -> list[Measurement]:
        """Return measurements for *indicator_name* within the given date range."""
        return self._repo.get_history(indicator_name, from_date, to_date)
