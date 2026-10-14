"""MarketLens - Responsible Scraping Safeguards Module.

Enforces ethical data collection principles:
1. robots.txt adherence & crawl-delay discovery (RFC 9309).
2. Access restriction detection (401, 403, 429, CAPTCHA markers).
3. Non-circumvention policy: Halts and reports rather than attempting evasion.
4. PII protection: Identifies and flags sensitive email/phone patterns.
"""

from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import logging
import re
import requests

logger = logging.getLogger("marketlens.safeguards")

# Common CAPTCHA and anti-bot challenge markers
CAPTCHA_MARKERS = [
    "cf-browser-verification",
    "cf-challenge",
    "g-recaptcha",
    "hcaptcha",
    "challenge-running",
    "attention required! | cloudflare",
    "datadome",
    "distil_identification_block",
]

# Sensitive Personal Identifiable Information (PII) regex patterns
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


class RobotsChecker:
    """Checks and respects target website robots.txt rules."""

    def __init__(self, user_agent: str):
        self.user_agent = user_agent
        self._parsers = {}

    def get_parser(self, base_url: str) -> Optional[RobotFileParser]:
        """Fetch and parse robots.txt for a given domain."""
        parsed_url = urlparse(base_url)
        domain_root = f"{parsed_url.scheme}://{parsed_url.netloc}"

        if domain_root in self._parsers:
            return self._parsers[domain_root]

        robots_url = urljoin(domain_root, "/robots.txt")
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            resp = requests.get(robots_url, headers={"User-Agent": self.user_agent}, timeout=5)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
                logger.info("Found and parsed robots.txt for: %s", domain_root)
            elif resp.status_code == 404:
                # 404 means no crawl restrictions are published
                logger.debug("No robots.txt found (HTTP 404) for %s. Crawling allowed.", domain_root)
                parser.allow_all = True
            else:
                logger.warning("robots.txt returned HTTP %d for %s. Defaulting to polite access.", resp.status_code, domain_root)
                parser.allow_all = True
        except Exception as e:
            logger.warning("Could not retrieve robots.txt from %s (%s). Proceeding politely.", domain_root, e)
            parser.allow_all = True

        self._parsers[domain_root] = parser
        return parser

    def is_allowed(self, target_url: str) -> bool:
        """Verify if our User-Agent is permitted to scrape target_url."""
        parser = self.get_parser(target_url)
        if not parser:
            return True

        allowed = parser.can_fetch(self.user_agent, target_url)
        if not allowed:
            logger.error(
                "Access blocked by robots.txt! User-Agent '%s' is disallowed from crawling: %s",
                self.user_agent,
                target_url,
            )
        return allowed

    def get_crawl_delay(self, target_url: str) -> Optional[float]:
        """Check if robots.txt specifies a recommended crawl delay."""
        parser = self.get_parser(target_url)
        if parser:
            delay = parser.crawl_delay(self.user_agent)
            if delay:
                logger.info("robots.txt requested crawl delay of %.1f second(s) for %s", delay, target_url)
                return float(delay)
        return None


class EthicalScrapingGuard:
    """Enforces non-circumvention rules and detects access blocks."""

    @staticmethod
    def inspect_response(response: requests.Response) -> Tuple[bool, Optional[str]]:
        """Inspect HTTP response for access restriction barriers.
        
        Returns:
            Tuple of (can_proceed: bool, restriction_reason: Optional[str])
        """
        # 1. Status Code Check
        if response.status_code in (401, 403):
            reason = f"Access Restricted: HTTP {response.status_code} ({response.reason}). Server actively blocked request."
            logger.error("%s - Halting per ethical non-circumvention policy.", reason)
            return False, reason

        if response.status_code == 429:
            reason = "Rate Limited: HTTP 429 Too Many Requests. Server requested crawler to halt."
            logger.error("%s - Halting to prevent server overload.", reason)
            return False, reason

        # 2. CAPTCHA / Cloudflare Challenge Detection in HTML Body
        content_lower = response.text.lower() if response.text else ""
        for marker in CAPTCHA_MARKERS:
            if marker in content_lower:
                reason = f"Automated Security Barrier Detected: Found challenge marker '{marker}'."
                logger.error("%s - Stopping immediately. MarketLens does NOT bypass security controls.", reason)
                return False, reason

        return True, None

    @staticmethod
    def audit_record_for_pii(record: dict) -> Tuple[bool, list]:
        """Audit an extracted record to ensure sensitive PII was not unintentionally collected."""
        flagged = []
        for key, value in record.items():
            if isinstance(value, str):
                if EMAIL_PATTERN.search(value):
                    flagged.append(f"Potential Email PII in field '{key}'")
                if PHONE_PATTERN.search(value):
                    flagged.append(f"Potential Phone Number PII in field '{key}'")
        return len(flagged) == 0, flagged
