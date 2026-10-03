"""Entry point for Economist Raider."""

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv  # type: ignore[import-untyped]

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/economist_raider.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def build_dependencies():
    """Compose and return all application dependencies."""
    from economist_raider.infrastructure.db import connection as db
    from economist_raider.adapters.repositories.sqlite_indicator_repository import (
        SQLiteIndicatorRepository,
    )
    from economist_raider.adapters.repositories.sqlite_source_repository import (
        SQLiteSourceRepository,
    )

    db.configure(DB_PATH)

    indicator_repo = SQLiteIndicatorRepository()
    source_repo = SQLiteSourceRepository()
    return indicator_repo, source_repo


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Economist Raider — Observatorio Económico de Colombia"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize or migrate the local database and exit",
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Run a manual data collection from all sources and exit",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Limit --collect to a specific source name",
    )
    parser.add_argument(
        "--no-scheduler",
        action="store_true",
        help="Start the UI without the automatic update scheduler",
    )
    args = parser.parse_args()

    indicator_repo, source_repo = build_dependencies()

    if args.init_db:
        from economist_raider.infrastructure.db import connection as db_conn
        db_conn.get_connection()  # triggers migration
        logger.info("Database initialized at %s", DB_PATH)
        return

    if args.collect:
        from economist_raider.application.use_cases.update_source_data import (
            UpdateSourceData,
        )
        from economist_raider.adapters.scrapers.banrep_scraper import BanrepScraper
        from economist_raider.adapters.scrapers.dane_scraper import DaneScraper

        scrapers = {
            "banrep": BanrepScraper(),
            "dane": DaneScraper(),
        }
        use_case = UpdateSourceData(indicator_repo, source_repo)
        targets = (
            {args.source: scrapers[args.source]}
            if args.source and args.source in scrapers
            else scrapers
        )
        for name, scraper in targets.items():
            logger.info("Collecting from %s...", name)
            use_case.execute(scraper)
        return

    # Start UI
    from economist_raider.infrastructure.ui.app import start_app

    start_app(
        indicator_repo=indicator_repo,
        source_repo=source_repo,
        enable_scheduler=not args.no_scheduler,
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
