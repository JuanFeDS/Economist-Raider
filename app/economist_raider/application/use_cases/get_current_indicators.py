"""Use case: retrieve the latest value for each active indicator."""

from economist_raider.domain.entities.indicator import Indicator
from economist_raider.domain.ports.indicator_repository import IndicatorRepository


class GetCurrentIndicators:
    def __init__(self, indicator_repo: IndicatorRepository) -> None:
        self._repo = indicator_repo

    def execute(self) -> list[Indicator]:
        """Return latest non-quarantined indicator per name, sorted by category."""
        return self._repo.get_all_latest()
