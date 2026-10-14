"""MarketLens - Quotes to Scrape Data Source Adapter.

Demonstrates multi-source reusability using permitted practice sandbox:
https://quotes.toscrape.com/
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
import logging
from bs4 import BeautifulSoup
from marketlens.sources.base import BaseSource

logger = logging.getLogger("marketlens.sources.quotes")


class QuotesSource(BaseSource):
    """Adapter for scraping and processing quote records from quotes.toscrape.com."""

    @property
    def source_name(self) -> str:
        return "quotes"

    @property
    def base_url(self) -> str:
        return "https://quotes.toscrape.com/"

    def parse_items(self, html_content: str, current_url: str) -> List[Dict[str, Any]]:
        """Parse quote cards from quotes.toscrape.com."""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        quote_cards = soup.select("div.quote")
        logger.info("Identified %d quote items on %s", len(quote_cards), current_url)

        records: List[Dict[str, Any]] = []
        for card in quote_cards:
            # 1. Text
            text_el = card.select_one("span.text")
            # Strip standard and smart quotes
            quote_text = text_el.get_text(strip=True).strip("“”\"'") if text_el else ""

            # 2. Author
            author_el = card.select_one("small.author")
            author = author_el.get_text(strip=True) if author_el else "Unknown"

            # 3. Author Profile URL
            author_link = card.select_one("span a[href*='/author/']")
            author_url = urljoin(current_url, author_link.get("href")) if author_link else ""

            # 4. Tags
            tag_els = card.select("div.tags a.tag")
            tags = ", ".join([t.get_text(strip=True) for t in tag_els])

            # 5. Extraction Timestamp
            timestamp = datetime.now(timezone.utc).isoformat()

            records.append({
                "quote_text": quote_text,
                "author": author,
                "author_url": author_url,
                "tags": tags,
                "source_url": current_url,
                "extraction_timestamp": timestamp,
            })

        return records

    def extract_next_page_url(self, html_content: str, current_url: str) -> Optional[str]:
        """Locate pagination control on quotes.toscrape.com."""
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")
        next_button = soup.select_one("li.next a")
        if not next_button:
            return None

        relative_href = next_button.get("href")
        return urljoin(current_url, relative_href) if relative_href else None

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate quote record integrity."""
        errors: List[str] = []
        text = record.get("quote_text", "")
        if not text or len(str(text).strip()) < 5:
            errors.append("Quote text is missing or shorter than 5 characters")

        author = record.get("author", "")
        if not author or len(str(author).strip()) < 2:
            errors.append("Author name is missing or invalid")

        return len(errors) == 0, errors

    def clean_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize quote record fields."""
        return {
            "quote_text": str(raw_record.get("quote_text", "")).strip(),
            "author": str(raw_record.get("author", "")).strip(),
            "author_url": str(raw_record.get("author_url", "")).strip(),
            "tags": str(raw_record.get("tags", "")).strip(),
            "source_url": str(raw_record.get("source_url", "")).strip(),
            "extraction_timestamp": str(raw_record.get("extraction_timestamp", "")).strip(),
        }

    def get_unique_key(self, raw_record: Dict[str, Any]) -> str:
        """Composite unique key: quote_text + author."""
        text = str(raw_record.get("quote_text", "")).lower().strip()
        author = str(raw_record.get("author", "")).lower().strip()
        return f"{author}::{text}"
