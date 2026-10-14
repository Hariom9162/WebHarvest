"""MarketLens - Phase 5 Data Cleaning & Validation Pipeline Runner.

Demonstrates:
1. Loading raw scraped data from data/raw/books_raw.csv.
2. Injecting edge-case test records (duplicate and invalid) to test robustness.
3. Executing deduplication and validation business rules.
4. Exporting accepted records to data/processed/books_cleaned.csv.
5. Exporting rejected records to data/processed/rejected_records.csv.
"""

from pathlib import Path
import csv
import sys

# Ensure src/ is on Python's module search path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from marketlens.cleaner import clean_and_validate_dataset


RAW_INPUT_FILE = Path("data") / "raw" / "books_raw.csv"
CLEAN_OUTPUT_FILE = Path("data") / "processed" / "books_cleaned.csv"
REJECTED_OUTPUT_FILE = Path("data") / "processed" / "rejected_records.csv"


def load_raw_csv(filepath: Path) -> list:
    """Load raw records from a CSV file."""
    if not filepath.exists():
        print(f"[ERROR] Raw data file not found: {filepath}", file=sys.stderr)
        return []

    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv(records: list, filepath: Path) -> None:
    """Save records to a CSV file safely."""
    if not records:
        return
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0].keys())
    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def run_phase5_pipeline() -> None:
    print("=" * 65)
    print("MarketLens: Phase 5 - Data Cleaning and Validation Pipeline")
    print("=" * 65)

    # 1. Load raw data
    raw_records = load_raw_csv(RAW_INPUT_FILE)
    print(f"[INPUT] Loaded {len(raw_records)} records from: {RAW_INPUT_FILE}")

    if not raw_records:
        print("[ERROR] Please run 'scraper.py' first to generate raw data.", file=sys.stderr)
        return

    # 2. Add 2 deliberate edge-cases to prove detection works live
    print("\n[STRESS TEST] Injecting 2 deliberate anomalies to test detection:")
    
    # Anomaly A: Exact Duplicate of record #1
    duplicate_item = dict(raw_records[0])
    raw_records.append(duplicate_item)
    print(f"  + Injected Duplicate: '{duplicate_item.get('title')}'")

    # Anomaly B: Invalid Record (corrupted price and missing title)
    corrupted_item = {
        "title": " ",
        "price": "OUT_OF_STOCK_UNKNOWN",
        "availability": "",
        "product_url": "not-a-valid-url",
        "rating": "None",
        "source_url": "https://books.toscrape.com/",
        "extraction_timestamp": "2026-10-15T00:00:00Z",
    }
    raw_records.append(corrupted_item)
    print(f"  + Injected Corrupted Item: Invalid URL, blank title, non-numeric price")

    print(f"\n[PIPELINE] Processing {len(raw_records)} total records through validation & cleaner...")

    # 3. Clean and Validate
    accepted, rejected, stats = clean_and_validate_dataset(raw_records)

    # 4. Save Outputs
    save_csv(accepted, CLEAN_OUTPUT_FILE)
    save_csv(rejected, REJECTED_OUTPUT_FILE)

    # 5. Display Audit Summary
    print("\n" + "=" * 65)
    print("DATA QUALITY AUDIT REPORT")
    print("=" * 65)
    print(f"Total Input Records      : {stats['total_input_records']}")
    print(f"Accepted Cleaned Records : {stats['accepted_records']}")
    print(f"Rejected Records         : {stats['rejected_records']}")
    print(f"  - Duplicates Removed   : {stats['duplicates_removed']}")
    print(f"  - Validation Failures  : {stats['validation_failures']}")
    print("-" * 65)
    print(f"[SUCCESS] Cleaned data saved  : {CLEAN_OUTPUT_FILE}")
    print(f"[SUCCESS] Rejected data saved : {REJECTED_OUTPUT_FILE}")
    print("=" * 65)


if __name__ == "__main__":
    run_phase5_pipeline()
