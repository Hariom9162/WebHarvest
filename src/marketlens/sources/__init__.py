"""MarketLens - Source Adapters Registry & Factory."""

from typing import Dict, Type
from marketlens.sources.base import BaseSource
from marketlens.sources.books_source import BooksSource
from marketlens.sources.quotes_source import QuotesSource

SOURCE_REGISTRY: Dict[str, Type[BaseSource]] = {
    "books": BooksSource,
    "quotes": QuotesSource,
}


def get_source_adapter(name: str) -> BaseSource:
    """Factory function to instantiate a registered source adapter.
    
    Args:
        name: Name of the source ('books', 'quotes').
        
    Returns:
        An instance of BaseSource.
        
    Raises:
        ValueError: If source name is not recognized.
    """
    source_class = SOURCE_REGISTRY.get(name.lower())
    if not source_class:
        available = ", ".join(list(SOURCE_REGISTRY.keys()))
        raise ValueError(f"Unknown data source '{name}'. Available sources: {available}")
    return source_class()
