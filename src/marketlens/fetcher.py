"""MarketLens - Network Fetcher Module with Ethical Safeguards.

Responsible for executing polite HTTP requests with timeouts,
robots.txt verification, anti-bot challenge detection, and non-circumvention rules.
"""

from typing import Optional
import logging
import time
import requests
from marketlens.safeguards import EthicalScrapingGuard, RobotsChecker

logger = logging.getLogger("marketlens.fetcher")


class PageFetcher:
    """Manages HTTP requests with session reuse, robots.txt checks, and ethical safeguards."""

    def __init__(self, user_agent: str, default_timeout: int = 10, respect_robots: bool = True):
        self.user_agent = user_agent
        self.default_timeout = default_timeout
        self.respect_robots = respect_robots
        self.robots_checker = RobotsChecker(user_agent) if respect_robots else None

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def fetch(self, url: str, timeout: Optional[int] = None) -> Optional[str]:
        """Fetch HTML content from a URL with ethical safeguards and detailed logging."""
        request_timeout = timeout or self.default_timeout

        # Safeguard 1: robots.txt permission check
        if self.robots_checker and not self.robots_checker.is_allowed(url):
            logger.error("Skipping %s: Disallowed by target website's robots.txt rules.", url)
            return None

        logger.info("Requesting URL: %s (timeout: %ds)", url, request_timeout)
        start_time = time.time()

        try:
            response = self.session.get(url, timeout=request_timeout)
            elapsed = time.time() - start_time
            logger.debug(
                "Received HTTP %d for %s in %.2fs (%d bytes)",
                response.status_code,
                url,
                elapsed,
                len(response.content),
            )

            # Safeguard 2: Access restriction & CAPTCHA detection
            can_proceed, reason = EthicalScrapingGuard.inspect_response(response)
            if not can_proceed:
                logger.error("Access Restriction Encountered on %s: %s", url, reason)
                return None

            response.raise_for_status()

            # Ensure UTF-8 decoding for currency symbols
            if response.encoding and response.encoding.lower() in ("iso-8859-1", "ascii"):
                response.encoding = response.apparent_encoding or "utf-8"

            return response.text

        except requests.exceptions.Timeout:
            logger.error("Request timed out after %ds while connecting to: %s", request_timeout, url)
            return None
        except requests.exceptions.HTTPError as err:
            logger.error("HTTP error encountered for URL: %s -> %s", url, err)
            return None
        except requests.exceptions.ConnectionError as err:
            logger.error("Failed to establish connection to: %s (DNS/Network failure: %s)", url, err)
            return None
        except requests.exceptions.RequestException as err:
            logger.error("Unexpected network error fetching %s: %s", url, err, exc_info=True)
            return None

    def close(self) -> None:
        """Close the underlying requests Session."""
        self.session.close()
