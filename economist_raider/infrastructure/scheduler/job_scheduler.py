"""APScheduler-based job scheduler — one job per active source."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from economist_raider.adapters.scrapers.base_scraper import BaseScraper, ScraperError
from economist_raider.application.use_cases.update_source_data import UpdateSourceData

logger = logging.getLogger(__name__)

_FREQUENCY_TO_SECONDS = {
    "daily": 86_400,
    "monthly": 86_400 * 30,
    "quarterly": 86_400 * 90,
    "hourly": 3_600,
}


class JobScheduler:
    def __init__(
        self,
        update_use_case: UpdateSourceData,
        scrapers: list[BaseScraper],
    ) -> None:
        self._use_case = update_use_case
        self._scrapers = scrapers
        self._scheduler = BackgroundScheduler(timezone="America/Bogota")

    def start(self) -> None:
        """Register one job per scraper and start the scheduler."""
        for scraper in self._scrapers:
            interval_seconds = _FREQUENCY_TO_SECONDS.get(
                getattr(scraper, "update_frequency", "daily"), 86_400
            )
            self._scheduler.add_job(
                func=self._run_scraper,
                trigger="interval",
                seconds=interval_seconds,
                args=[scraper],
                id=f"collect_{scraper.source_name}",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            logger.info(
                "Scheduled %s every %ds",
                scraper.source_name,
                interval_seconds,
            )

        self._scheduler.start()
        logger.info("Job scheduler started with %d job(s)", len(self._scrapers))

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Job scheduler stopped")

    def _run_scraper(self, scraper: BaseScraper) -> None:
        """Execute a scraper — isolated so one failure does not stop others."""
        try:
            logger.info("Scheduled run: %s", scraper.source_name)
            self._use_case.execute(scraper)
        except Exception as exc:
            logger.error(
                "Unhandled error in scheduled run for %s: %s",
                scraper.source_name,
                exc,
                exc_info=True,
            )
