"""MarketLens - Source Adapter Abstract Base Class.

Defines the contract that every data source adapter must implement.
Separates source-specific DOM parsing and validation from the reusable
fetching, pacing, deduplication, logging, and export engines.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseSource(ABC):
    """Abstract Base Class for all MarketLens scraping and extraction adapters."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this data source (e.g. 'books', 'quotes')."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """The entry point URL for this data source."""
        pass

    @abstractmethod
    def parse_items(self, html_content: str, current_url: str) -> List[Dict[str, Any]]:
        """Parse raw HTML and extract a list of raw entity dictionaries."""
        pass

    @abstractmethod
    def extract_next_page_url(self, html_content: str, current_url: str) -> Optional[str]:
        """Locate pagination control and return absolute URL for the next page."""
        pass

    @abstractmethod
    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate an individual record against source-specific integrity rules."""
        pass

    @abstractmethod
    def clean_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a raw entity dictionary into standardized, typed format."""
        pass

    @abstractmethod
    def get_unique_key(self, raw_record: Dict[str, Any]) -> str:
        """Return the composite canonical key used for duplicate detection."""
        pass
