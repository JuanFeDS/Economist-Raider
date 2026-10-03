"""Scraper for DANE (Departamento Administrativo Nacional de Estadística).

Extracts: IPC (monthly), Tasa de Desempleo (monthly), PIB Crecimiento (quarterly).
"""

import logging
from datetime import date
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

DANE_SOURCE_ID = UUID("22222222-2222-2222-2222-222222222222")

DANE_IPC_URL = "https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-precios-al-consumidor-ipc"
DANE_DESEMPLEO_URL = "https://www.dane.gov.co/index.php/estadisticas-por-tema/mercado-laboral/empleo-y-desempleo"
DANE_PIB_URL = "https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales"


class DaneScraper(BaseScraper):
    source_name = "DANE"
    base_url = "https://www.dane.gov.co"
    rate_limit_seconds = 2.0

    @property
    def source_info(self) -> Source:
        return Source(
            id=DANE_SOURCE_ID,
            name=self.source_name,
            source_type=SourceType.OFFICIAL_GOV,
            base_url=self.base_url,
            update_frequency="monthly",
        )

    def fetch(self) -> list[Indicator]:
        if not self.check_robots(self.base_url):
            raise RobotsDisallowedError(self.base_url)

        indicators: list[Indicator] = []

        for fetcher in (self._fetch_ipc, self._fetch_desempleo, self._fetch_pib):
            result = fetcher()
            if result:
                indicators.append(result)

        return indicators

    def _fetch_ipc(self) -> Indicator | None:
        """Fetch IPC (Índice de Precios al Consumidor) — monthly variation."""
        try:
            response = self.get(DANE_IPC_URL)
            soup = BeautifulSoup(response.text, "lxml")

            # DANE shows the latest IPC variation in a summary block
            value_el = soup.select_one(
                ".cifra-destacada, .indicador-valor, table.tabla-indicadores td:nth-child(2)"
            )
            if not value_el:
                logger.warning("DaneScraper: IPC element not found")
                return self._make_quarantined(
                    "IPC", IndicatorCategory.MACROECONOMIC,
                    "% variación mensual", PeriodType.MONTHLY,
                    "IPC element not found in DANE page"
                )

            raw = value_el.get_text(strip=True).replace("%", "").replace(",", ".").strip()
            value = Decimal(raw)

            indicator = Indicator(
                name="IPC",
                category=IndicatorCategory.MACROECONOMIC,
                value=value,
                unit="% variación mensual",
                measured_at=_first_day_of_current_month(),
                period_type=PeriodType.MONTHLY,
                source_id=DANE_SOURCE_ID,
            )
            valid, reason = self.validate(indicator)
            if not valid:
                return indicator.model_copy(
                    update={"is_quarantined": True, "quarantine_reason": reason}
                )
            return indicator

        except Exception as exc:
            logger.error("DaneScraper: Failed to fetch IPC: %s", exc)
            return self._make_quarantined(
                "IPC", IndicatorCategory.MACROECONOMIC,
                "% variación mensual", PeriodType.MONTHLY, str(exc)
            )

    def _fetch_desempleo(self) -> Indicator | None:
        """Fetch Tasa de Desempleo — monthly."""
        try:
            response = self.get(DANE_DESEMPLEO_URL)
            soup = BeautifulSoup(response.text, "lxml")

            value_el = soup.select_one(
                ".cifra-destacada, .indicador-valor"
            )
            if not value_el:
                logger.warning("DaneScraper: Desempleo element not found")
                return self._make_quarantined(
                    "Tasa de Desempleo", IndicatorCategory.LABOR,
                    "%", PeriodType.MONTHLY,
                    "Desempleo element not found in DANE page"
                )

            raw = value_el.get_text(strip=True).replace("%", "").replace(",", ".").strip()
            value = Decimal(raw)

            indicator = Indicator(
                name="Tasa de Desempleo",
                category=IndicatorCategory.LABOR,
                value=value,
                unit="%",
                measured_at=_first_day_of_current_month(),
                period_type=PeriodType.MONTHLY,
                source_id=DANE_SOURCE_ID,
            )
            valid, reason = self.validate(indicator)
            if not valid:
                return indicator.model_copy(
                    update={"is_quarantined": True, "quarantine_reason": reason}
                )
            return indicator

        except Exception as exc:
            logger.error("DaneScraper: Failed to fetch Desempleo: %s", exc)
            return self._make_quarantined(
                "Tasa de Desempleo", IndicatorCategory.LABOR,
                "%", PeriodType.MONTHLY, str(exc)
            )

    def _fetch_pib(self) -> Indicator | None:
        """Fetch PIB Crecimiento — quarterly growth rate."""
        try:
            response = self.get(DANE_PIB_URL)
            soup = BeautifulSoup(response.text, "lxml")

            value_el = soup.select_one(
                ".cifra-destacada, .indicador-valor"
            )
            if not value_el:
                logger.warning("DaneScraper: PIB element not found")
                return self._make_quarantined(
                    "PIB Crecimiento", IndicatorCategory.MACROECONOMIC,
                    "% variación trimestral", PeriodType.QUARTERLY,
                    "PIB element not found in DANE page"
                )

            raw = value_el.get_text(strip=True).replace("%", "").replace(",", ".").strip()
            value = Decimal(raw)

            indicator = Indicator(
                name="PIB Crecimiento",
                category=IndicatorCategory.MACROECONOMIC,
                value=value,
                unit="% variación trimestral",
                measured_at=_first_day_of_current_month(),
                period_type=PeriodType.QUARTERLY,
                source_id=DANE_SOURCE_ID,
            )
            valid, reason = self.validate(indicator)
            if not valid:
                return indicator.model_copy(
                    update={"is_quarantined": True, "quarantine_reason": reason}
                )
            return indicator

        except Exception as exc:
            logger.error("DaneScraper: Failed to fetch PIB: %s", exc)
            return self._make_quarantined(
                "PIB Crecimiento", IndicatorCategory.MACROECONOMIC,
                "% variación trimestral", PeriodType.QUARTERLY, str(exc)
            )

    def _make_quarantined(
        self, name: str, category, unit: str,
        period_type: PeriodType, reason: str
    ) -> Indicator:
        return Indicator(
            name=name,
            category=category,
            value=Decimal("0"),
            unit=unit,
            measured_at=date.today(),
            period_type=period_type,
            source_id=DANE_SOURCE_ID,
            is_quarantined=True,
            quarantine_reason=reason,
        )


def _first_day_of_current_month() -> date:
    today = date.today()
    return today.replace(day=1)
