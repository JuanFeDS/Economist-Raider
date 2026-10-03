"""Stub scraper for Ministerio de Hacienda y Crédito Público.

Not yet implemented — source is registered as inactive.
"""

from uuid import UUID

from economist_raider.adapters.scrapers.base_scraper import BaseScraper
from economist_raider.domain.entities.indicator import Indicator

MINHACIENDA_SOURCE_ID = UUID("33333333-3333-3333-3333-333333333333")


class MinhaciendaScraper(BaseScraper):
    source_name = "Ministerio de Hacienda"
    base_url = "https://www.minhacienda.gov.co"
    rate_limit_seconds = 2.0

    def fetch(self) -> list[Indicator]:  # pragma: no cover
        # TODO: implement fiscal deficit, public debt indicators
        raise NotImplementedError(
            "MinhaciendaScraper is not yet implemented. "
            "Source is registered as inactive in the database."
        )
