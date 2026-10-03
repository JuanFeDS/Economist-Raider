"""Scraper for Banco de la República de Colombia.

Extracts: TRM (daily) and Tasa de Referencia (policy rate).
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from bs4 import BeautifulSoup

from economist_raider.adapters.scrapers.base_scraper import (
    BaseScraper,
    ParseError,
    RobotsDisallowedError,
)
from economist_raider.domain.entities.indicator import (
    Indicator,
    IndicatorCategory,
    PeriodType,
)
from economist_raider.domain.entities.source import Source, SourceType

logger = logging.getLogger(__name__)

# UUID fijo para identificar esta fuente en la base de datos
BANREP_SOURCE_ID = UUID("11111111-1111-1111-1111-111111111111")

# Banrep expone una API de series estadísticas
TRM_API_URL = (
    "https://www.banrep.gov.co/es/estadisticas/trm"
)
TASA_REF_URL = (
    "https://www.banrep.gov.co/es/estadisticas/tasas-de-interes-politica-monetaria"
)


class BanrepScraper(BaseScraper):
    source_name = "Banco de la República"
    base_url = "https://www.banrep.gov.co"
    rate_limit_seconds = 2.0

    @property
    def source_info(self) -> Source:
        return Source(
            id=BANREP_SOURCE_ID,
            name=self.source_name,
            source_type=SourceType.CENTRAL_BANK,
            base_url=self.base_url,
            update_frequency="daily",
        )

    def fetch(self) -> list[Indicator]:
        if not self.check_robots(self.base_url):
            raise RobotsDisallowedError(self.base_url)

        indicators: list[Indicator] = []

        trm = self._fetch_trm()
        if trm:
            indicators.append(trm)

        tasa = self._fetch_tasa_referencia()
        if tasa:
            indicators.append(tasa)

        return indicators

    def _fetch_trm(self) -> Indicator | None:
        """Fetch TRM (Tasa Representativa del Mercado) from Banrep."""
        try:
            # Banrep has a public JSON endpoint for TRM
            url = (
                "https://www.banrep.gov.co/es/estadisticas/trm"
            )
            response = self.get(url)
            soup = BeautifulSoup(response.text, "lxml")

            # Look for the TRM value in the page
            value_el = soup.select_one(".field--name-field-valor-trm")
            date_el = soup.select_one(".field--name-field-fecha-trm")

            if not value_el or not date_el:
                logger.warning("BanrepScraper: TRM elements not found in page")
                return self._make_quarantined(
                    "TRM", "MONETARY", "COP/USD", PeriodType.DAILY,
                    "TRM element not found in page"
                )

            raw_value = value_el.get_text(strip=True).replace(",", "").replace("$", "").strip()
            raw_date = date_el.get_text(strip=True)

            value = Decimal(raw_value)
            measured_at = _parse_banrep_date(raw_date)

            indicator = Indicator(
                name="TRM",
                category=IndicatorCategory.MONETARY,
                value=value,
                unit="COP/USD",
                measured_at=measured_at,
                period_type=PeriodType.DAILY,
                source_id=BANREP_SOURCE_ID,
            )
            valid, reason = self.validate(indicator)
            if not valid:
                return indicator.model_copy(
                    update={"is_quarantined": True, "quarantine_reason": reason}
                )
            return indicator

        except Exception as exc:
            logger.error("BanrepScraper: Failed to fetch TRM: %s", exc)
            return self._make_quarantined(
                "TRM", IndicatorCategory.MONETARY, "COP/USD",
                PeriodType.DAILY, str(exc)
            )

    def _fetch_tasa_referencia(self) -> Indicator | None:
        """Fetch Tasa de Referencia (policy interest rate) from Banrep."""
        try:
            response = self.get(TASA_REF_URL)
            soup = BeautifulSoup(response.text, "lxml")

            # Banrep shows the current rate in a prominent element
            rate_el = soup.select_one(".tasa-politica-valor, .field--name-body table tr:first-child td:last-child")
            if not rate_el:
                logger.warning("BanrepScraper: Tasa de Referencia element not found")
                return self._make_quarantined(
                    "Tasa de Referencia", IndicatorCategory.MONETARY,
                    "% EA", PeriodType.MONTHLY,
                    "Rate element not found in page"
                )

            raw_value = rate_el.get_text(strip=True).replace("%", "").replace(",", ".").strip()
            value = Decimal(raw_value)

            indicator = Indicator(
                name="Tasa de Referencia",
                category=IndicatorCategory.MONETARY,
                value=value,
                unit="% EA",
                measured_at=date.today(),
                period_type=PeriodType.MONTHLY,
                source_id=BANREP_SOURCE_ID,
            )
            valid, reason = self.validate(indicator)
            if not valid:
                return indicator.model_copy(
                    update={"is_quarantined": True, "quarantine_reason": reason}
                )
            return indicator

        except Exception as exc:
            logger.error("BanrepScraper: Failed to fetch Tasa de Referencia: %s", exc)
            return self._make_quarantined(
                "Tasa de Referencia", IndicatorCategory.MONETARY,
                "% EA", PeriodType.MONTHLY, str(exc)
            )

    def _make_quarantined(
        self, name: str, category, unit: str,
        period_type: PeriodType, reason: str
    ) -> Indicator:
        from decimal import Decimal
        return Indicator(
            name=name,
            category=category,
            value=Decimal("0"),
            unit=unit,
            measured_at=date.today(),
            period_type=period_type,
            source_id=BANREP_SOURCE_ID,
            is_quarantined=True,
            quarantine_reason=reason,
        )


def _parse_banrep_date(raw: str) -> date:
    """Parse Banrep date formats. Falls back to today on failure."""
    import re
    # Try ISO format first
    try:
        return date.fromisoformat(raw.strip())
    except ValueError:
        pass
    # Try DD/MM/YYYY
    match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw.strip())
    if match:
        d, m, y = match.groups()
        return date(int(y), int(m), int(d))
    logger.warning("BanrepScraper: Could not parse date '%s', using today", raw)
    return date.today()
