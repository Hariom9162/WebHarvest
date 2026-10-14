"""MarketLens - Cleaner Unit Tests.

Tests text stripping, price parsing, rating mapping,
deduplication, and dataset transformation.
"""

import pytest
from marketlens.cleaner import (
    clean_availability,
    clean_record,
    clean_text,
    clean_and_validate_dataset,
    parse_price,
    parse_rating,
)


def test_clean_text() -> None:
    """Test trimming whitespace and collapsing internal spaces."""
    assert clean_text("  Clean   Text  ") == "Clean Text"
    assert clean_text("NoChange") == "NoChange"
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_parse_price() -> None:
    """Test extracting float prices from currency strings."""
    assert parse_price("£51.77") == 51.77
    assert parse_price("$19.99") == 19.99
    assert parse_price("€1,250.50") == 1250.50
    assert parse_price("42.00") == 42.00
    assert parse_price(35.5) == 35.5
    assert parse_price("Not Numeric") is None
    assert parse_price(None) is None


def test_parse_rating() -> None:
    """Test converting string star ratings to numeric integers."""
    assert parse_rating("One") == 1
    assert parse_rating("Two") == 2
    assert parse_rating("Three") == 3
    assert parse_rating("Four") == 4
    assert parse_rating("Five") == 5
    assert parse_rating("Unknown") == 0
    assert parse_rating(None) == 0


def test_clean_availability() -> None:
    """Test normalizing availability status."""
    is_stock, label = clean_availability("In stock")
    assert is_stock is True
    assert label == "In Stock"

    is_stock, label = clean_availability("Out of stock")
    assert is_stock is False
    assert label == "Out of Stock"


def test_duplicate_removal() -> None:
    """Test that records with identical product URLs are deduplicated."""
    raw_records = [
        {
            "title": "Book A",
            "price": "£10.00",
            "availability": "In stock",
            "product_url": "https://books.toscrape.com/book-a",
            "rating": "Five",
            "source_url": "https://books.toscrape.com/",
            "extraction_timestamp": "2026-10-15T00:00:00Z",
        },
        {
            "title": "Book A (Duplicate Entry)",
            "price": "£10.00",
            "availability": "In stock",
            "product_url": "https://books.toscrape.com/book-a",
            "rating": "Five",
            "source_url": "https://books.toscrape.com/",
            "extraction_timestamp": "2026-10-15T00:01:00Z",
        },
    ]

    accepted, rejected, stats = clean_and_validate_dataset(raw_records)
    assert len(accepted) == 1
    assert len(rejected) == 1
    assert stats["duplicates_removed"] == 1
    assert "Duplicate record detected" in rejected[0]["rejection_reason"]
