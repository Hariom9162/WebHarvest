"""MarketLens - HTML Parser Module.

Extracts structured book items and pagination controls from raw HTML documents
using BeautifulSoup and CSS selectors, with diagnostic warnings for missing nodes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("marketlens.parser")


class BookParser:
    """Parses book products and pagination links from HTML markup."""

    @staticmethod
    def extract_single_card(card: BeautifulSoup, source_url: str, card_index: int = 0) -> Dict[str, Any]:
        """Extract fields from a single product card with diagnostic logging."""
        # 1. Title
        title_tag = card.select_one("h3 a")
        title = None
        if title_tag:
            title = title_tag.get("title") or title_tag.get_text(strip=True)
        else:
            logger.warning("Card #%d is missing an <h3> <a> title element.", card_index)

        # 2. Price
        price_tag = card.select_one("p.price_color")
        price = price_tag.get_text(strip=True) if price_tag else ""
        if not price:
            logger.warning("Card #%d ('%s') has empty or missing price.", card_index, title or "Unknown")

        # 3. Availability
        stock_tag = card.select_one("p.instock.availability")
        availability = stock_tag.get_text(strip=True) if stock_tag else ""

        # 4. Product URL
        relative_href = title_tag.get("href") if title_tag else ""
        product_url = urljoin(source_url, relative_href) if relative_href else ""

        # 5. Rating
        rating_tag = card.select_one("p.star-rating")
        rating_classes = rating_tag.get("class", []) if rating_tag else []
        rating_words = [c for c in rating_classes if c != "star-rating"]
        rating = rating_words[0] if rating_words else "Not Rated"

        # 6. Extraction Metadata
        extraction_timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "title": title,
            "price": price,
            "availability": availability,
            "product_url": product_url,
            "rating": rating,
            "source_url": source_url,
            "extraction_timestamp": extraction_timestamp,
        }

    @classmethod
    def parse_books(cls, html_content: str, source_url: str) -> List[Dict[str, Any]]:
        """Parse all book cards from an HTML document."""
        if not html_content:
            logger.warning("Empty HTML string provided to parse_books.")
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        cards = soup.select("article.product_pod")
        logger.info("Identified %d book cards on %s", len(cards), source_url)

        records: List[Dict[str, Any]] = []
        for idx, card in enumerate(cards, start=1):
            record = cls.extract_single_card(card, source_url, card_index=idx)
            records.append(record)

        return records

    @staticmethod
    def extract_next_page_url(html_content: str, current_page_url: str) -> Optional[str]:
        """Locate the pagination 'Next' link and return the resolved absolute URL."""
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")
        next_button = soup.select_one("li.next a")
        if not next_button:
            logger.debug("No 'next' pagination element found on: %s", current_page_url)
            return None

        relative_href = next_button.get("href")
        if not relative_href:
            return None

        next_url = urljoin(current_page_url, relative_href)
        logger.debug("Resolved next page target: %s", next_url)
        return next_url
