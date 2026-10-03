"""NiceGUI application entry point."""

from economist_raider.domain.ports.indicator_repository import IndicatorRepository
from economist_raider.domain.ports.source_repository import SourceRepository


def start_app(
    indicator_repo: IndicatorRepository,
    source_repo: SourceRepository,
    enable_scheduler: bool = True,
    port: int = 8080,
) -> None:
    """Configure and launch the NiceGUI dashboard."""
    from nicegui import app, ui

    from economist_raider.infrastructure.ui.pages.dashboard import create_dashboard
    from economist_raider.adapters.scrapers.banrep_scraper import BanrepScraper
    from economist_raider.adapters.scrapers.dane_scraper import DaneScraper
    from economist_raider.application.use_cases.update_source_data import UpdateSourceData

    scrapers = [BanrepScraper(), DaneScraper()]
    update_use_case = UpdateSourceData(indicator_repo, source_repo)

    def collect_all() -> None:
        for scraper in scrapers:
            update_use_case.execute(scraper)

    create_dashboard(indicator_repo, source_repo, collect_fn=collect_all)

    if enable_scheduler:
        _start_scheduler(update_use_case, scrapers)

    ui.run(
        title="Observatorio Económico — Colombia",
        port=port,
        reload=False,
        show=False,
        favicon="📊",
    )


def _start_scheduler(update_use_case, scrapers: list) -> None:
    from economist_raider.infrastructure.scheduler.job_scheduler import JobScheduler

    scheduler = JobScheduler(update_use_case, scrapers)
    scheduler.start()
