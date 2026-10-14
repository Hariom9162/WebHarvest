"""MarketLens - Books to Scrape Data Source Adapter.

Implements BaseSource for https://books.toscrape.com/
"""

from typing import Any, Dict, List, Optional, Tuple
from marketlens.cleaner import clean_record
from marketlens.parser import BookParser
from marketlens.sources.base import BaseSource
from marketlens.validators import validate_book_record


class BooksSource(BaseSource):
    """Adapter for scraping and processing books from books.toscrape.com."""

    @property
    def source_name(self) -> str:
        return "books"

    @property
    def base_url(self) -> str:
        return "https://books.toscrape.com/"

    def parse_items(self, html_content: str, current_url: str) -> List[Dict[str, Any]]:
        return BookParser.parse_books(html_content, current_url)

    def extract_next_page_url(self, html_content: str, current_url: str) -> Optional[str]:
        return BookParser.extract_next_page_url(html_content, current_url)

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        return validate_book_record(record)

    def clean_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        return clean_record(raw_record)

    def get_unique_key(self, raw_record: Dict[str, Any]) -> str:
        url = raw_record.get("product_url", "")
        return str(url).strip().lower()
