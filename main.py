"""MarketLens - CLI Application Entry Point.

Provides a unified Command-Line Interface (CLI) to orchestrate:
- Web scraping across single or multiple pages
- Configurable output formats (CSV, Excel, or both)
- Data validation & cleaning pipelines
- Offline demonstration mode (no live network required)
- Execution summary reports
"""

from pathlib import Path
from typing import Any, Dict, List
import argparse
import sys
import time

# Ensure UTF-8 output in Windows PowerShell for currency symbols
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root and src/ are importable
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import (
    BASE_URL,
    CLEANED_CSV_PATH,
    CLEANED_XLSX_PATH,
    DEFAULT_MAX_PAGES,
    DEFAULT_REQUEST_DELAY,
    DEFAULT_TIMEOUT,
    PROCESSED_DATA_DIR,
    RAW_CSV_PATH,
    RAW_DATA_DIR,
    REJECTED_CSV_PATH,
    REPORT_CHART_PATH,
    REPORT_RATING_CSV_PATH,
    REPORT_TXT_PATH,
    USER_AGENT,
    setup_logging,
)
from marketlens.analytics import (
    generate_market_metrics,
    generate_visual_charts,
    save_text_report,
)
from marketlens.cleaner import clean_and_validate_dataset
from marketlens.exporter import export_dataset, export_to_csv
from marketlens.fetcher import PageFetcher
from marketlens.parser import BookParser
from marketlens.sources import get_source_adapter
import pandas as pd

# Bundled sample HTML for offline demonstration mode
OFFLINE_DEMO_HTML = """
<!DOCTYPE html>
<html>
<body>
<div class="page_inner">
    <article class="product_pod">
        <h3><a href="catalogue/sample-book-1_100/index.html" title="Data Analytics Fundamentals">Data Analytics...</a></h3>
        <p class="star-rating Five"><i class="icon-star"></i></p>
        <div class="product_price">
            <p class="price_color">£39.99</p>
            <p class="instock availability"><i class="icon-ok"></i> In stock</p>
        </div>
    </article>
    <article class="product_pod">
        <h3><a href="catalogue/sample-book-2_99/index.html" title="Python Web Scraping Handbook">Python Web Scraping...</a></h3>
        <p class="star-rating Four"><i class="icon-star"></i></p>
        <div class="product_price">
            <p class="price_color">£45.50</p>
            <p class="instock availability"><i class="icon-ok"></i> In stock</p>
        </div>
    </article>
    <article class="product_pod">
        <h3><a href="catalogue/sample-book-3_98/index.html" title="Market Research Strategy Guide">Market Research...</a></h3>
        <p class="star-rating Three"><i class="icon-star"></i></p>
        <div class="product_price">
            <p class="price_color">£28.00</p>
            <p class="instock availability"><i class="icon-ok"></i> In stock</p>
        </div>
    </article>
</div>
</body>
</html>
"""


def run_pipeline(
    source_name: str = "books",
    max_pages: int = DEFAULT_MAX_PAGES,
    delay: float = DEFAULT_REQUEST_DELAY,
    output_format: str = "both",
    validate_only: bool = False,
    demo_mode: bool = False,
    show_report: bool = True,
) -> int:
    """Orchestrate data scraping, validation, cleaning, and exporting."""
    logger = setup_logging()

    print("\n" + "=" * 68)
    print(f"MarketLens: Automated Data Pipeline [Source: {source_name.upper()}]")
    print("=" * 68)

    adapter = get_source_adapter(source_name)
    raw_csv_target = RAW_CSV_PATH if source_name == "books" else RAW_DATA_DIR / f"{source_name}_raw.csv"
    clean_base_target = (PROCESSED_DATA_DIR / f"{source_name}_cleaned")

    raw_records: List[Dict[str, Any]] = []

    # -------------------------------------------------------------
    # Step 1: Data Acquisition (Live Scrape, Demo, or Validate-Only)
    # -------------------------------------------------------------
    if demo_mode:
        print("[MODE] Running in OFFLINE DEMONSTRATION MODE (no internet access required)...")
        logger.info("Executing offline demonstration mode using bundled sample markup.")
        raw_records = adapter.parse_items(OFFLINE_DEMO_HTML, "https://demo.marketlens.local/")
        if raw_records:
            raw_records.append(dict(raw_records[0]))
        print(f"[DEMO] Parsed {len(raw_records)} demo records (including 1 deliberate duplicate).")

    elif validate_only:
        print(f"[MODE] VALIDATE-ONLY MODE: Reading existing raw file: {raw_csv_target}")
        if not raw_csv_target.exists():
            logger.error("Raw data file does not exist: %s. Run scraping first.", raw_csv_target)
            print(f"[ERROR] Cannot validate: {raw_csv_target} not found. Run 'python main.py --pages 1' first.")
            return 1

        import csv
        with open(raw_csv_target, mode="r", encoding="utf-8-sig") as f:
            raw_records = list(csv.DictReader(f))
        print(f"[LOAD] Loaded {len(raw_records)} records from raw landing zone.")

    else:
        # Live Web Scraping using Selected Source Adapter
        target_url = adapter.base_url
        print(f"[MODE] LIVE SCRAPING: Crawling up to {max_pages} page(s) from {target_url}")
        logger.info("Initiating live crawl for '%s': MaxPages=%d, Delay=%.1fs", source_name, max_pages, delay)
        fetcher = PageFetcher(user_agent=USER_AGENT, default_timeout=DEFAULT_TIMEOUT)

        current_url = target_url
        pages_crawled = 0

        try:
            while current_url and pages_crawled < max_pages:
                pages_crawled += 1
                print(f"  -> [Page {pages_crawled}/{max_pages}] Fetching: {current_url}")
                html = fetcher.fetch(current_url)

                if not html:
                    print(f"  [ERROR] Network error on {current_url}. Stopping crawl gracefully.")
                    break

                page_items = adapter.parse_items(html, current_url)
                raw_records.extend(page_items)
                print(f"     Extracted {len(page_items)} {source_name} items. Total collected: {len(raw_records)}")

                next_url = adapter.extract_next_page_url(html, current_url)
                if next_url and pages_crawled < max_pages:
                    time.sleep(delay)
                    current_url = next_url
                else:
                    current_url = None

        finally:
            fetcher.close()

        # Save Raw Snapshot
        export_to_csv(raw_records, raw_csv_target)
        print(f"[RAW DATA] Persisted {len(raw_records)} raw records to: {raw_csv_target}")

    if not raw_records:
        print("[WARNING] No records available for processing. Exiting.")
        return 0

    # -------------------------------------------------------------
    # Step 2: Cleaning, Validation, and Deduplication
    # -------------------------------------------------------------
    print(f"\n[ENGINE] Cleaning and validating {len(raw_records)} records...")
    if source_name == "books":
        accepted, rejected, stats = clean_and_validate_dataset(raw_records)
    else:
        # Generic multi-source cleaning and validation using Adapter methods
        accepted = []
        rejected = []
        seen_keys = set()
        dup_count = 0
        val_fail_count = 0
        for idx, rec in enumerate(raw_records, start=1):
            is_valid, errors = adapter.validate_record(rec)
            if not is_valid:
                val_fail_count += 1
                rej = dict(rec)
                rej["rejection_reason"] = "; ".join(errors)
                rejected.append(rej)
                continue
            key = adapter.get_unique_key(rec)
            if key in seen_keys:
                dup_count += 1
                rej = dict(rec)
                rej["rejection_reason"] = f"Duplicate key: {key}"
                rejected.append(rej)
                continue
            seen_keys.add(key)
            accepted.append(adapter.clean_record(rec))
        stats = {
            "total_input_records": len(raw_records),
            "accepted_records": len(accepted),
            "rejected_records": len(rejected),
            "duplicates_removed": dup_count,
            "validation_failures": val_fail_count,
        }

    # -------------------------------------------------------------
    # Step 3: Export Deliverables
    # -------------------------------------------------------------
    formats_to_export = ["csv", "xlsx"] if output_format == "both" else [output_format]
    print(f"[EXPORT] Writing deliverables in format(s): {formats_to_export}")

    export_results = export_dataset(
        accepted,
        clean_base_target,
        formats=formats_to_export,
    )

    if rejected:
        export_to_csv(rejected, REJECTED_CSV_PATH)
        print(f"[REJECTED] {len(rejected)} invalid/duplicate record(s) logged to: {REJECTED_CSV_PATH}")

    # -------------------------------------------------------------
    # Step 4: Analytics, Metrics & Reports
    # -------------------------------------------------------------
    if accepted and source_name == "books":
        print(f"\n[ANALYTICS] Computing descriptive statistics & visualizations...")
        df_accepted = pd.DataFrame(accepted)
        metrics = generate_market_metrics(df_accepted, pipeline_stats=stats)

        # 4a. Save Executive Text Report
        save_text_report(metrics, REPORT_TXT_PATH)
        print(f"[REPORT] Executive research report saved: {REPORT_TXT_PATH}")

        # 4b. Save Rating Distribution Breakdown CSV
        rating_df = pd.DataFrame(
            list(metrics["rating_distribution"].items()),
            columns=["star_rating", "book_count"]
        )
        rating_df.to_csv(REPORT_RATING_CSV_PATH, index=False, encoding="utf-8-sig")
        print(f"[REPORT] Rating breakdown CSV saved: {REPORT_RATING_CSV_PATH}")

        # 4c. Generate Visual Charts (Price Histogram + Star Rating Bar Chart)
        chart_path = generate_visual_charts(df_accepted, REPORT_CHART_PATH)
        if chart_path:
            print(f"[REPORT] Visual market charts generated: {REPORT_CHART_PATH}")

        if show_report:
            print("\n" + "-" * 68)
            print("PIPELINE EXECUTION SUMMARY (BOOKS)")
            print("-" * 68)
            print(f"Total Records Input       : {stats['total_input_records']}")
            print(f"Accepted Cleaned Records  : {stats['accepted_records']}")
            print(f"Rejected Records          : {stats['rejected_records']}")
            print(f"  - Duplicates Removed    : {stats['duplicates_removed']}")
            print(f"  - Validation Failures   : {stats['validation_failures']}")
            print(f"Average Book Price        : £{metrics['mean_price_gbp']:.2f}")
            print(f"Median Book Price         : £{metrics['median_price_gbp']:.2f}")
            print(f"Price Range               : £{metrics['min_price_gbp']:.2f} - £{metrics['max_price_gbp']:.2f}")
            print(f"Catalog Valuation         : £{metrics['total_catalog_valuation_gbp']:,.2f}")
            for fmt, path in export_results.items():
                print(f"Deliverable ({fmt.upper()})        : {path}")
            print(f"Research Report (TXT)     : {REPORT_TXT_PATH}")
            if chart_path:
                print(f"Analytics Chart (PNG)     : {REPORT_CHART_PATH}")
            print("-" * 68)

    elif accepted and show_report:
        # Non-book source generic execution summary
        print("\n" + "-" * 68)
        print(f"PIPELINE EXECUTION SUMMARY ({source_name.upper()})")
        print("-" * 68)
        print(f"Total Records Input       : {stats['total_input_records']}")
        print(f"Accepted Cleaned Records  : {stats['accepted_records']}")
        print(f"Rejected Records          : {stats['rejected_records']}")
        print(f"  - Duplicates Removed    : {stats['duplicates_removed']}")
        print(f"  - Validation Failures   : {stats['validation_failures']}")
        for fmt, path in export_results.items():
            print(f"Deliverable ({fmt.upper()})        : {path}")
        print("-" * 68)

    print("\n[COMPLETE] MarketLens pipeline finished successfully!\n")
    return 0


def build_cli_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser with helpful documentation."""
    parser = argparse.ArgumentParser(
        prog="marketlens",
        description="MarketLens — Automated Web Scraping & Market Data Engineering Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --pages 3
  python main.py --pages 2 --format xlsx --delay 1.5
  python main.py --validate-only
  python main.py --demo
        """,
    )

    parser.add_argument(
        "-s", "--source",
        choices=["books", "quotes"],
        default="books",
        help="Data source adapter to scrape: 'books' or 'quotes' (default: books)",
    )

    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"Maximum number of pages to scrape (default: {DEFAULT_MAX_PAGES})",
    )

    parser.add_argument(
        "-f", "--format",
        choices=["csv", "xlsx", "both"],
        default="both",
        help="Export deliverable format: 'csv', 'xlsx', or 'both' (default: both)",
    )

    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=DEFAULT_REQUEST_DELAY,
        help=f"Polite delay in seconds between page requests (default: {DEFAULT_REQUEST_DELAY})",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Skip web scraping; clean and validate existing raw data in data/raw/books_raw.csv",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run offline demonstration pipeline using bundled sample data (no internet required)",
    )

    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Suppress terminal summary metrics report",
    )

    return parser


def main() -> None:
    """CLI application entry point."""
    parser = build_cli_parser()
    args = parser.parse_args()

    # Validate argument bounds
    if args.pages <= 0:
        parser.error("--pages must be a positive integer greater than 0.")
    if args.delay < 0:
        parser.error("--delay cannot be negative.")

    exit_code = run_pipeline(
        source_name=args.source,
        max_pages=args.pages,
        delay=args.delay,
        output_format=args.format,
        validate_only=args.validate_only,
        demo_mode=args.demo,
        show_report=not args.no_report,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
