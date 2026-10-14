"""MarketLens - Phase 7 Logging and Error Handling Demonstration.

Demonstrates:
1. Setting up dual-target logging (Terminal + logs/marketlens.log).
2. Logging scraper milestones, page transitions, and records extracted.
3. Graceful handling of network timeouts / invalid URLs with error logging.
4. Auditing duplicate detection and invalid records in log files.
5. Verifying log file creation and contents.
"""

from pathlib import Path
import sys
import time

# Ensure root and src are on path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import (
    BASE_URL,
    CLEANED_CSV_PATH,
    CLEANED_XLSX_PATH,
    LOG_FILE_PATH,
    RAW_CSV_PATH,
    REJECTED_CSV_PATH,
    USER_AGENT,
    setup_logging,
)
from marketlens.cleaner import clean_and_validate_dataset
from marketlens.exporter import export_dataset, export_to_csv
from marketlens.fetcher import PageFetcher
from marketlens.parser import BookParser


def run_phase7_pipeline(max_pages: int = 2) -> None:
    # 1. Initialize Logging
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("MarketLens Application Pipeline Started")
    logger.info("=" * 60)
    logger.info("Configuration: BaseURL=%s, MaxPages=%d, UserAgent=%s", BASE_URL, max_pages, USER_AGENT)

    fetcher = PageFetcher(user_agent=USER_AGENT, default_timeout=10)
    parser = BookParser()

    all_raw_records = []
    current_url = BASE_URL
    pages_crawled = 0

    try:
        # 2. Multi-page Crawl Loop with Logging
        while current_url and pages_crawled < max_pages:
            pages_crawled += 1
            logger.info("--- Processing Page %d of %d: %s ---", pages_crawled, max_pages, current_url)

            html = fetcher.fetch(current_url)
            if not html:
                logger.error("Failed to retrieve HTML for %s. Stopping crawl.", current_url)
                break

            page_records = parser.parse_books(html, current_url)
            all_raw_records.extend(page_records)
            logger.info("Page %d yielded %d records. Total so far: %d", pages_crawled, len(page_records), len(all_raw_records))

            next_url = parser.extract_next_page_url(html, current_url)
            if next_url and pages_crawled < max_pages:
                logger.debug("Next page link detected: %s. Pacing request (1.0s delay)...", next_url)
                time.sleep(1.0)
                current_url = next_url
            else:
                current_url = None

        # 3. Simulate and Demonstrate Error Handling
        logger.info("[DIAGNOSTIC TEST] Intentionally requesting an invalid URL to test error logging...")
        bad_url = "https://books.toscrape.com/this-page-does-not-exist-404.html"
        fetcher.fetch(bad_url)

        # 4. Save Raw Records
        logger.info("Saving raw extracted records to: %s", RAW_CSV_PATH)
        export_to_csv(all_raw_records, RAW_CSV_PATH)

        # 5. Clean, Deduplicate & Validate
        logger.info("Passing records through cleaning and validation engine...")
        # Inject deliberate duplicate for logging visibility
        if all_raw_records:
            all_raw_records.append(dict(all_raw_records[0]))

        accepted, rejected, stats = clean_and_validate_dataset(all_raw_records)

        # 6. Export Processed Data
        export_dataset(accepted, CLEANED_CSV_PATH.with_suffix(""), formats=["csv", "xlsx"])
        if rejected:
            export_to_csv(rejected, REJECTED_CSV_PATH)

        logger.info("Pipeline completed successfully! Accepted=%d, Rejected=%d", len(accepted), len(rejected))
        logger.info("=" * 60)

    except Exception as err:
        logger.critical("Uncaught critical exception in pipeline: %s", err, exc_info=True)
    finally:
        fetcher.close()


def print_log_sample(log_path: Path, lines: int = 15) -> None:
    """Print the last N lines of the log file for verification."""
    print(f"\n[LOG AUDIT] Inspecting recent entries in {log_path}:")
    print("-" * 75)
    if not log_path.exists():
        print("Log file not found.")
        return

    with open(log_path, mode="r", encoding="utf-8") as f:
        log_lines = f.readlines()
        for line in log_lines[-lines:]:
            print(line.rstrip())
    print("-" * 75)


if __name__ == "__main__":
    run_phase7_pipeline(max_pages=2)
    print_log_sample(LOG_FILE_PATH, lines=16)
