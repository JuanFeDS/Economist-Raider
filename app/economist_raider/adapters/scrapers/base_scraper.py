"""Base scraper contract with robots.txt check and rate-limiting."""

import time
from abc import ABC, abstractmethod
from decimal import Decimal
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from economist_raider.domain.entities.indicator import Indicator


class ScraperError(Exception):
    """Base error for all scraper failures."""


class RobotsDisallowedError(ScraperError):
    """Raised when robots.txt disallows scraping."""


class SourceUnreachableError(ScraperError):
    """Raised when the source cannot be reached."""


class ParseError(ScraperError):
    """Raised when the response cannot be parsed."""


# Validation ranges by indicator name
_VALIDATION_RANGES: dict[str, tuple[float, float]] = {
    "IPC": (-5.0, 50.0),
    "TRM": (1_000.0, 10_000.0),
    "Tasa de Referencia": (0.0, 30.0),
    "Tasa de Desempleo": (0.0, 50.0),
    "PIB Crecimiento": (-20.0, 20.0),
}


class BaseScraper(ABC):
    source_name: str
    base_url: str
    user_agent: str = (
        "EconomistRaider/1.0 (+https://github.com/economist-raider)"
    )
    rate_limit_seconds: float = 1.0

    @property
    def source_info(self):
        """Return a Source entity describing this scraper's data source.

        Subclasses must override this to provide their Source metadata.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement source_info"
        )

    _last_request_time: float = 0.0

    @abstractmethod
    def fetch(self) -> list[Indicator]:
        """
        Connect to the source, extract and return validated indicators.

        - MUST check robots.txt before the first request
        - MUST respect rate_limit_seconds between consecutive requests
        - MUST return quarantined indicators for invalid data (no exceptions)
        - MUST raise SourceUnreachableError if the source is unreachable
        """

    def check_robots(self, url: str) -> bool:
        """Return True if scraping is allowed by robots.txt."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
        except Exception:
            # If robots.txt cannot be read, allow scraping by default
            return True
        return rp.can_fetch(self.user_agent, url)

    def get(self, url: str, **kwargs) -> httpx.Response:
        """Rate-limited HTTP GET with honest User-Agent."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        try:
            with httpx.Client(
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
                timeout=15.0,
            ) as client:
                response = client.get(url, **kwargs)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SourceUnreachableError(
                f"Failed to reach {url}: {exc}"
            ) from exc
        finally:
            self._last_request_time = time.monotonic()
        return response

    def validate(self, indicator: Indicator) -> tuple[bool, str | None]:
        """Validate indicator value against known ranges."""
        ranges = _VALIDATION_RANGES.get(indicator.name)
        if ranges is None:
            return True, None
        lo, hi = ranges
        try:
            val = float(indicator.value)
        except (ValueError, TypeError):
            return False, f"Non-numeric value: {indicator.value}"
        if not (lo <= val <= hi):
            return False, (
                f"Value {val} out of expected range [{lo}, {hi}] "
                f"for indicator '{indicator.name}'"
            )
        return True, None
