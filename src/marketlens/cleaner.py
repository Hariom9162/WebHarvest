"""MarketLens - Data Cleaning and Deduplication Module.

Transforms raw scraped data into consistent, typed, analytics-ready formats.
Removes duplicate records, standardizes text casing, parses numerical values,
and separates accepted records from rejected records with logged reasons.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import logging
import re
from marketlens.validators import validate_book_record

logger = logging.getLogger("marketlens.cleaner")

# Mapping textual star ratings to numeric ratings (1-5)
RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def clean_text(text: Optional[str]) -> str:
    """Strip unnecessary whitespace and collapse multiple internal spaces."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip())


def parse_price(raw_price: Any) -> Optional[float]:
    """Convert raw price strings (e.g., '£51.77', '€1,250.50') into clean float values."""
    if raw_price is None:
        return None
    if isinstance(raw_price, (int, float)):
        return round(float(raw_price), 2)

    # Remove commas first so numbers like '1,250.50' become '1250.50'
    clean_str = str(raw_price).replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)", clean_str)
    if match:
        try:
            return round(float(match.group(1)), 2)
        except ValueError:
            return None
    return None


def parse_rating(raw_rating: Any) -> int:
    """Convert star rating strings (e.g., 'Three') into integer stars (1-5)."""
    if isinstance(raw_rating, int):
        return raw_rating if 1 <= raw_rating <= 5 else 0

    rating_str = clean_text(str(raw_rating)).lower()
    return RATING_MAP.get(rating_str, 0)


def clean_availability(raw_availability: Any) -> Tuple[bool, str]:
    """Normalize availability text and extract a boolean flag."""
    text = clean_text(str(raw_availability or "")).lower()
    if "in stock" in text or "available" in text:
        return True, "In Stock"
    return False, "Out of Stock"


def clean_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and standardize an individual raw book record into analytics format."""
    is_in_stock, stock_status = clean_availability(raw.get("availability"))
    
    return {
        "title": clean_text(raw.get("title")),
        "price_gbp": parse_price(raw.get("price")),
        "rating_stars": parse_rating(raw.get("rating")),
        "is_in_stock": is_in_stock,
        "availability": stock_status,
        "product_url": clean_text(raw.get("product_url")),
        "source_url": clean_text(raw.get("source_url")),
        "extraction_timestamp": clean_text(raw.get("extraction_timestamp")),
    }


def clean_and_validate_dataset(
    raw_records: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """Clean a batch of raw records, remove duplicates, and validate business rules."""
    logger.info("Starting cleaning & validation on %d input records", len(raw_records))
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    seen_unique_keys: Set[str] = set()

    duplicates_count = 0
    validation_failures_count = 0

    for idx, raw in enumerate(raw_records, start=1):
        # 1. Validation check on raw fields
        is_valid, validation_errors = validate_book_record(raw)
        if not is_valid:
            validation_failures_count += 1
            error_msg = "; ".join(validation_errors)
            logger.warning("Record #%d rejected: %s", idx, error_msg)
            rejected_item = dict(raw)
            rejected_item["rejection_reason"] = error_msg
            rejected_item["record_index"] = idx
            rejected.append(rejected_item)
            continue

        # 2. Duplicate detection using product_url
        unique_key = clean_text(raw.get("product_url")).lower()
        if unique_key in seen_unique_keys:
            duplicates_count += 1
            logger.warning("Record #%d duplicate dropped (URL: %s)", idx, unique_key)
            rejected_item = dict(raw)
            rejected_item["rejection_reason"] = f"Duplicate record detected (URL already processed: {unique_key})"
            rejected_item["record_index"] = idx
            rejected.append(rejected_item)
            continue

        seen_unique_keys.add(unique_key)

        # 3. Apply cleaning transformations
        cleaned = clean_record(raw)
        accepted.append(cleaned)

    stats = {
        "total_input_records": len(raw_records),
        "accepted_records": len(accepted),
        "rejected_records": len(rejected),
        "duplicates_removed": duplicates_count,
        "validation_failures": validation_failures_count,
    }

    logger.info(
        "Cleaning finished: %d accepted, %d rejected (%d duplicates, %d invalid)",
        stats["accepted_records"],
        stats["rejected_records"],
        stats["duplicates_removed"],
        stats["validation_failures"],
    )

    return accepted, rejected, stats
