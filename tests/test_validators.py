"""MarketLens - Validator Unit Tests.

Tests business integrity validation rules, URL syntax checking,
and rejection error messaging.
"""

import pytest
from marketlens.validators import is_valid_url, validate_book_record


def test_is_valid_url() -> None:
    """Test URL format validation."""
    assert is_valid_url("https://books.toscrape.com/book_1.html") is True
    assert is_valid_url("http://localhost:8000/test") is True
    assert is_valid_url("ftp://not-supported.com") is False
    assert is_valid_url("just-a-string") is False
    assert is_valid_url("") is False
    assert is_valid_url(None) is False


def test_validate_valid_record() -> None:
    """Test that a complete, correct record passes validation."""
    record = {
        "title": "Automate the Boring Stuff with Python",
        "price": "£25.00",
        "availability": "In stock",
        "product_url": "https://books.toscrape.com/automate_123.html",
        "rating": "Five",
    }
    is_valid, errors = validate_book_record(record)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_missing_or_short_title() -> None:
    """Test rejection when title is missing or less than 2 characters."""
    record_none = {
        "title": None,
        "price": "£10.00",
        "availability": "In stock",
        "product_url": "https://books.toscrape.com/item.html",
    }
    is_valid, errors = validate_book_record(record_none)
    assert is_valid is False
    assert any("title" in err.lower() for err in errors)

    record_short = dict(record_none, title=" ")
    is_valid, errors = validate_book_record(record_short)
    assert is_valid is False


def test_validate_invalid_price() -> None:
    """Test rejection when price cannot be converted to a positive float."""
    record_bad_price = {
        "title": "Good Title",
        "price": "PRICE_UNAVAILABLE",
        "availability": "In stock",
        "product_url": "https://books.toscrape.com/item.html",
    }
    is_valid, errors = validate_book_record(record_bad_price)
    assert is_valid is False
    assert any("price" in err.lower() for err in errors)


def test_validate_negative_price() -> None:
    """Test rejection when price is negative."""
    record_neg = {
        "title": "Good Title",
        "price": -15.50,
        "availability": "In stock",
        "product_url": "https://books.toscrape.com/item.html",
    }
    is_valid, errors = validate_book_record(record_neg)
    assert is_valid is False
    assert any("negative" in err.lower() for err in errors)
