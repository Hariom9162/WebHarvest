"""MarketLens - Data Validation Module.

Defines business rules and integrity checks for scraped market records.
Identifies invalid, missing, or corrupted data fields before they enter
analytics pipelines or database stores.
"""

from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse


VALID_RATING_WORDS = {"one", "two", "three", "four", "five", "not rated"}


def is_valid_url(url: Any) -> bool:
    """Validate whether a value is a valid HTTP or HTTPS URL."""
    if not isinstance(url, str) or not url.strip():
        return False
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def validate_book_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate an individual book record against business integrity rules.
    
    Validation Rules:
    1. Title must be a non-empty string with at least 2 characters.
    2. Price must exist and be convertible to a non-negative float.
    3. Product URL must be a valid HTTP or HTTPS web address.
    4. Availability must not be completely empty.
    
    Args:
        record: Dictionary containing the record fields.
        
    Returns:
        Tuple containing:
        - bool: True if the record passed all checks, False otherwise.
        - List[str]: A list of failure reasons (empty if valid).
    """
    errors: List[str] = []

    # Rule 1: Validate Title
    title = record.get("title")
    if title is None or not isinstance(title, str) or len(title.strip()) < 2:
        errors.append("Missing or invalid title (must have at least 2 characters)")

    # Rule 2: Validate Price
    price = record.get("price")
    if price is None:
        errors.append("Price field is missing (None)")
    elif isinstance(price, (int, float)):
        if price < 0:
            errors.append(f"Price cannot be negative: {price}")
    elif isinstance(price, str):
        # Attempt preliminary check if it's a numeric string or currency string
        cleaned_str = price.replace("£", "").replace("$", "").replace("€", "").replace(",", "").strip()
        try:
            val = float(cleaned_str)
            if val < 0:
                errors.append(f"Price cannot be negative: {val}")
        except ValueError:
            errors.append(f"Price string cannot be parsed as a number: '{price}'")
    else:
        errors.append(f"Price has unsupported type: {type(price).__name__}")

    # Rule 3: Validate Product URL
    product_url = record.get("product_url")
    if not is_valid_url(product_url):
        errors.append(f"Invalid product URL: '{product_url}'")

    # Rule 4: Validate Availability
    availability = record.get("availability")
    if availability is None or not str(availability).strip():
        errors.append("Availability status is missing")

    is_valid = len(errors) == 0
    return is_valid, errors
