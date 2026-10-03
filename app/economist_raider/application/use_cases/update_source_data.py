"""Use case: orchestrate data collection from a scraper."""

import logging

from economist_raider.adapters.scrapers.base_scraper import BaseScraper, ScraperError
from economist_raider.domain.entities.collection_run import CollectionRun
from economist_raider.domain.entities.source import RunStatus
from economist_raider.domain.ports.indicator_repository import IndicatorRepository
from economist_raider.domain.ports.source_repository import SourceRepository

logger = logging.getLogger(__name__)


class UpdateSourceData:
    def __init__(
        self,
        indicator_repo: IndicatorRepository,
        source_repo: SourceRepository,
    ) -> None:
        self._indicators = indicator_repo
        self._sources = source_repo

    def execute(self, scraper: BaseScraper) -> CollectionRun:
        """
        Run a scraper, validate results, persist indicators, and log the run.
        A failure in this source does NOT propagate — caller gets the run record.
        """
        # Auto-register the source if it doesn't exist yet
        self._sources.upsert(scraper.source_info)

        source_id = scraper.source_info.id
        run = CollectionRun(source_id=source_id)
        self._sources.update_run_status(source_id, RunStatus.RUNNING)

        try:
            indicators = scraper.fetch()
        except ScraperError as exc:
            logger.error("Collection failed for %s: %s", scraper.source_name, exc)
            run.fail(str(exc))
            self._sources.update_run_status(source_id, RunStatus.FAILED, str(exc))
            self._sources.save_collection_run(run)
            return run

        collected = 0
        quarantined = 0

        for indicator in indicators:
            if indicator.is_quarantined:
                logger.warning(
                    "Quarantined indicator %s: %s",
                    indicator.name,
                    indicator.quarantine_reason,
                )
                quarantined += 1
            else:
                self._indicators.save(indicator)
                collected += 1

        run.complete(collected, quarantined)
        self._sources.update_run_status(source_id, RunStatus.SUCCESS)
        self._sources.save_collection_run(run)

        logger.info(
            "Collection complete for %s: %d collected, %d quarantined",
            scraper.source_name,
            collected,
            quarantined,
        )
        return run


