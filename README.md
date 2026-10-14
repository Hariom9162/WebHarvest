# MarketLens: Python Web Scraping & Market Data Automation

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Tests Passing](https://img.shields.io/badge/pytest-27%20passed-brightgreen.svg)](https://pytest.org/)
[![Code Architecture](https://img.shields.io/badge/Architecture-Modular%20Adapter%20Pattern-orange.svg)](#architecture--system-design)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An enterprise-style, end-to-end Python web scraping, data validation, and market research automation system built from scratch. Designed as a practical work sample demonstrating skills required for a **Research Data Analyst (Web Data & Automation)** role at a market research or strategy consulting firm.

---

## 1. Project Overview & Problem Statement

### The Business Problem
Market research and strategy consulting teams frequently need to monitor competitor pricing, catalog updates, customer sentiment, and inventory trends across public digital marketplaces. However, naive scraping scripts suffer from several critical shortcomings:
* **Fragile Extraction:** Unchecked CSS selectors and unhandled `NoneType` errors crash batch jobs when website structures change.
* **Corrupted Deliverables:** Unescaped commas in CSVs, garbled currency symbols (`Â£`), and raw unformatted spreadsheets make data unpresentable to executive stakeholders.
* **Silent Data Loss:** Inexperienced scrapers silently discard invalid rows without logging rejection reasons, leaving analysts blind to data completeness.
* **Aggressive Crawling:** Lack of pacing or `robots.txt` compliance risks IP blacklisting and violates responsible scraping ethics.

### The MarketLens Solution
MarketLens solves these challenges with a resilient, modular architecture that decouples network fetching from DOM parsing, enforces schema validation rules, logs duplicate and invalid records with audit reasons, exports styled corporate Excel workbooks with freeze panes, and computes statistical market intelligence with Matplotlib visual distribution charts.

> **Demonstration Data Notice:** This project uses public sandbox websites (`https://books.toscrape.com/` and `https://quotes.toscrape.com/`) designed specifically for web scraping education and benchmark testing.

---

## 2. Key Features

- **Multi-Source Adapter Architecture:** Decoupled design using an Abstract Base Class (`BaseSource`) allows onboarding new data sources without rewriting core networking, exporting, or logging engines.
- **Defensive DOM Extraction:** Fault-tolerant CSS selector parsing that safely handles missing tags, unclipt titles, relative URLs, and word-based ratings.
- **Automated Pagination & Loop Prevention:** Tracks crawled URLs in an in-memory `set` to eliminate infinite loops and supports configurable page limits.
- **Data Validation & Deduplication:** Rejects invalid rows (blank titles, non-numeric or negative prices) and routes duplicates to a dead-letter log (`rejected_records.csv`) with clear audit explanations.
- **Consulting-Grade Deliverables:**
  - Standardized UTF-8-sig CSV files (`books_cleaned.csv`).
  - Professional Microsoft Excel workbooks (`books_cleaned.xlsx`) with corporate navy blue branding, auto-fitted column widths, currency formats (`£#,##0.00`), and frozen header panes (`A2`).
- **Descriptive Analytics & Visualizations:** Computes mean, median, standard deviation, catalog valuations, and rating distributions using pandas, and generates publication-grade PNG charts with Matplotlib.
- **Structured Dual-Destination Logging:** Clean terminal updates for operators paired with persistent, timestamped, line-number audit trails in `logs/marketlens.log`.
- **Ethical Safeguards:** Built-in `robots.txt` verification (RFC 9309), crawl-delay compliance, and non-circumvention rules that halt upon detecting HTTP 403, 429, or CAPTCHA challenges.
- **Offline Demonstration Mode:** Includes bundled sample HTML fixtures (`python main.py --demo`) enabling presentations without live internet access.
- **Automated Unit Test Suite:** 27 hermetic unit tests with 100% network independence executing in under 2 seconds.

---

## 3. Technology Stack

| Component | Library / Tool | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.13+ | Core programming and automation logic |
| **HTTP Requests** | `requests` (>=2.31.0) | Network communication, session pooling, custom User-Agents |
| **HTML Parsing** | `beautifulsoup4` (>=4.12.0) | CSS selector extraction and DOM tree traversal |
| **Data Processing** | `pandas` (>=2.0.0) | Tabular transformations, metrics, and aggregations |
| **Excel Automation** | `openpyxl` (>=3.1.0) | Custom workbook styling, freeze panes, and column sizing |
| **Configuration** | `python-dotenv` (>=1.0.0) | Environment variable management via `.env` |
| **Testing** | `pytest` (>=8.0.0) | Hermetic automated unit tests and fixtures |
| **Logging** | Python `logging` (Standard Lib) | Dual console + timestamped file logging |
| **Visualisation** | `matplotlib` (>=3.8.0) | Headless publication-quality market analytics charts |
| **Version Control** | Git & GitHub | Modular branching, code hygiene, and portfolio release |

---

## 4. Architecture & System Design

```text
                                 [ User / CLI ]
                                       │
                                   main.py
                                       │
                   ┌───────────────────┴───────────────────┐
                   ▼                                       ▼
           PageFetcher (fetcher.py)             Source Adapter Factory
                   │                            (sources/__init__.py)
     ┌─────────────┴─────────────┐                         │
     ▼                           ▼                         ▼
robots.txt Check         Ethical Guard             BaseSource (base.py)
(safeguards.py)         (safeguards.py)                    │
                                            ┌──────────────┴──────────────┐
                                            ▼                             ▼
                                       BooksSource                  QuotesSource
                                            │
                                  Raw Extracted Records
                                            │
                                            ▼
                                Cleaner & Validator Engine
                                  (cleaner.py / validators.py)
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
             Accepted Records                              Rejected Records
                     │                                (rejected_records.csv)
       ┌─────────────┴─────────────┐
       ▼                           ▼
Exporter Module             Analytics Engine
 (exporter.py)               (analytics.py)
       │                           │
 ┌─────┴─────┐               ┌─────┴─────┐
 ▼           ▼               ▼           ▼
CSV        Excel       Text Report   PNG Chart
```

### Directory Structure

```text
marketlens-python-web-scraper/
├── .env.example              # Environment variables template
├── .gitignore                # Protects .venv, local secrets, and generated data
├── config.py                 # Central settings, directory resolution, and logging setup
├── requirements.txt          # Pinned project dependencies
├── README.md                 # Complete system documentation
├── scraper.py                # Standalone baseline scraper demonstration
├── main.py                   # Master CLI entry point
├── data/
│   ├── raw/                  # Immutable landing zone for raw scraped data
│   │   └── .gitkeep
│   ├── processed/            # Cleaned, validated, and deduplicated datasets
│   │   └── .gitkeep
│   └── reports/              # Executive text reports and Matplotlib charts
│       └── .gitkeep
├── logs/                     # Persistent audit logs
│   └── .gitkeep
├── src/
│   └── marketlens/
│       ├── __init__.py       # Package definition
│       ├── analytics.py      # Statistical metrics, text reports, and chart rendering
│       ├── cleaner.py        # Text normalization, price parsing, and deduplication
│       ├── exporter.py       # Styled Excel and UTF-8-sig CSV export automation
│       ├── fetcher.py        # Resilient HTTP fetcher with connection reuse
│       ├── parser.py         # Fault-tolerant BeautifulSoup DOM parser
│       ├── safeguards.py     # robots.txt parser, challenge detection, PII audit
│       ├── validators.py     # Schema and business rule validation
│       └── sources/          # Pluggable Source Adapters
│           ├── __init__.py   # Source registry and factory
│           ├── base.py       # BaseSource Abstract Base Class
│           ├── books_source.py
│           └── quotes_source.py
└── tests/
    ├── __init__.py
    ├── conftest.py           # Pytest path and fixture configuration
    ├── test_cleaner.py       # Deduplication and parsing tests
    ├── test_exporter.py      # CSV and Excel output tests
    ├── test_parser.py        # DOM node and pagination tests
    ├── test_safeguards.py    # robots.txt and ethics barrier tests
    ├── test_sources.py       # Source adapter contract tests
    └── test_validators.py    # Data integrity validation tests
```

---

## 5. Installation Instructions (Windows PowerShell)

### Prerequisites
* Python 3.11, 3.12, or 3.13 installed (`python --version`)
* Git installed (`git --version`)

### Step 1: Clone the Repository
```powershell
git clone https://github.com/ankittdevlab/marketlens-python-web-scraper.git
cd marketlens-python-web-scraper
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If script execution is disabled on your machine, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once in PowerShell).*

### Step 3: Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Local Settings
```powershell
Copy-Item .env.example .env
```

---

## 6. How to Run the Project

### A. Run in Offline Demo Mode (No Internet Needed)
Runs the entire pipeline using bundled sample HTML data without making live network calls:
```powershell
python main.py --demo
```

### B. Live Scraping (Default: Books, 2 Pages)
Crawls 2 pages from `books.toscrape.com`, validates, deduplicates, and exports CSV, Excel, text report, and chart:
```powershell
python main.py --pages 2
```

### C. Live Scraping with Custom Options
Scrape 3 pages with a polite 1.5-second pacing delay and export Excel only:
```powershell
python main.py --pages 3 --format xlsx --delay 1.5
```

### D. Run Alternate Data Source (Quotes Adapter)
Scrapes quotes, authors, and tags from `quotes.toscrape.com`:
```powershell
python main.py --source quotes --pages 1
```

### E. Run Validation-Only Mode
Cleans, validates, and re-exports an existing raw file without re-scraping:
```powershell
python main.py --validate-only
```

---

## 7. Sample Outputs

### Terminal Execution Summary
```text
====================================================================
MarketLens: Automated Data Pipeline [Source: BOOKS]
====================================================================
[MODE] LIVE SCRAPING: Crawling up to 2 page(s) from https://books.toscrape.com/
[INFO] Initiating live crawl: MaxPages=2, Delay=1.0s
  -> [Page 1/2] Fetching: https://books.toscrape.com/
     Extracted 20 books. Total collected: 20
  -> [Page 2/2] Fetching: https://books.toscrape.com/catalogue/page-2.html
     Extracted 20 books. Total collected: 40
[RAW DATA] Persisted 40 raw records to: data/raw/books_raw.csv

[ENGINE] Cleaning and validating 40 records...
[EXPORT] Writing deliverables in format(s): ['csv', 'xlsx']
[INFO] Exported CSV successfully: data/processed/books_cleaned.csv (40 rows)
[INFO] Exported Excel workbook successfully: data/processed/books_cleaned.xlsx (40 rows)

[ANALYTICS] Computing descriptive statistics & visualizations...
[REPORT] Executive research report saved: data/reports/market_summary_report.txt
[REPORT] Rating breakdown CSV saved: data/reports/rating_distribution.csv
[REPORT] Visual market charts generated: data/reports/market_analytics_chart.png

--------------------------------------------------------------------
PIPELINE EXECUTION SUMMARY (BOOKS)
--------------------------------------------------------------------
Total Records Input       : 40
Accepted Cleaned Records  : 40
Rejected Records          : 0
  - Duplicates Removed    : 0
  - Validation Failures   : 0
Average Book Price        : £34.96
Median Book Price         : £34.08
Price Range               : £12.84 - £57.25
Catalog Valuation         : £1,398.35
Deliverable (CSV)        : data/processed/books_cleaned.csv
Deliverable (XLSX)        : data/processed/books_cleaned.xlsx
Research Report (TXT)     : data/reports/market_summary_report.txt
Analytics Chart (PNG)     : data/reports/market_analytics_chart.png
--------------------------------------------------------------------
[COMPLETE] MarketLens pipeline finished successfully!
```

### Executive Market Report (`data/reports/market_summary_report.txt`)
```text
====================================================================
              MARKETLENS DATA RESEARCH REPORT
        Automated Market Research & Strategy Deliverable
====================================================================

1. DATA COLLECTION & INGESTION AUDIT
   - Total Cleaned Records Analyzed : 40
   - Unique Product Titles          : 40
   - Duplicate Records Removed      : 0
   - Rejected Corrupted Records     : 0

2. PRICE & VALUATION ANALYSIS (GBP)
   - Average (Mean) Price           : £34.96
   - Median Price                   : £34.08
   - Price Range (Min - Max)        : £12.84 - £57.25
   - Standard Deviation             : £14.11
   - Total Catalog Value            : £1,398.35

3. INVENTORY & AVAILABILITY
   - In Stock Items                 : 40 (100.0%)
   - Out of Stock Items             : 0 (0.0%)

4. STAR RATING DISTRIBUTION
   - 1 Star(s) :   9 ( 22.5%)  ████
   - 2 Star(s) :   6 ( 15.0%)  ███
   - 3 Star(s) :   9 ( 22.5%)  ████
   - 4 Star(s) :   6 ( 15.0%)  ███
   - 5 Star(s) :  10 ( 25.0%)  █████

====================================================================
Generated automatically by MarketLens Analytics Engine
====================================================================
```

### Dead-Letter Queue (`data/processed/rejected_records.csv`)
When corrupted rows or duplicate links are encountered, they are routed to this log:
```csv
title,price,availability,product_url,rating,source_url,extraction_timestamp,rejection_reason,record_index
A Light in the Attic,£51.77,In stock,https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html,Three,https://books.toscrape.com/,2026-10-14T22:16:55Z,Duplicate record detected (URL already processed: ...),41
 ,OUT_OF_STOCK_UNKNOWN,,not-a-valid-url,None,https://books.toscrape.com/,2026-10-15T00:00:00Z,Missing or invalid title; Price string cannot be parsed as a number; Invalid product URL; Availability status is missing,42
```

---

## 8. Automated Testing

The project maintains an automated unit test suite with 27 test cases covering all modules. Tests utilize local HTML fixtures and pytest’s `tmp_path` fixture for zero network dependency.

To execute the test suite:
```powershell
pytest -v
```

Expected output:
```text
tests/test_cleaner.py::test_clean_text PASSED                            [  3%]
tests/test_cleaner.py::test_parse_price PASSED                           [  7%]
tests/test_cleaner.py::test_parse_rating PASSED                          [ 11%]
tests/test_cleaner.py::test_clean_availability PASSED                    [ 14%]
tests/test_cleaner.py::test_duplicate_removal PASSED                     [ 18%]
tests/test_exporter.py::test_export_to_csv PASSED                        [ 22%]
tests/test_exporter.py::test_export_to_excel_styling PASSED              [ 25%]
tests/test_exporter.py::test_export_empty_dataset PASSED                 [ 29%]
tests/test_exporter.py::test_export_dataset_both_formats PASSED          [ 33%]
tests/test_parser.py::test_parse_valid_book_card PASSED                  [ 37%]
tests/test_parser.py::test_parse_missing_elements_does_not_crash PASSED  [ 40%]
tests/test_parser.py::test_pagination_next_url_extracted PASSED          [ 44%]
tests/test_parser.py::test_pagination_returns_none_when_no_next_link PASSED [ 48%]
tests/test_parser.py::test_empty_html_handling PASSED                    [ 51%]
tests/test_safeguards.py::test_ethical_guard_detects_403_and_429 PASSED  [ 55%]
tests/test_safeguards.py::test_ethical_guard_detects_captcha_challenge PASSED [ 59%]
tests/test_safeguards.py::test_pii_audit_detection PASSED                [ 62%]
tests/test_safeguards.py::test_robots_checker_mock PASSED                [ 66%]
tests/test_sources.py::test_factory_get_source_adapter PASSED            [ 70%]
tests/test_sources.py::test_factory_invalid_source_raises_value_error PASSED [ 74%]
tests/test_sources.py::test_quotes_source_parsing PASSED                 [ 77%]
tests/test_sources.py::test_quotes_source_validation_and_cleaning PASSED [ 81%]
tests/test_validators.py::test_is_valid_url PASSED                       [ 85%]
tests/test_validators.py::test_validate_valid_record PASSED              [ 88%]
tests/test_validators.py::test_validate_missing_or_short_title PASSED    [ 92%]
tests/test_validators.py::test_validate_invalid_price PASSED             [ 96%]
tests/test_validators.py::test_validate_negative_price PASSED            [100%]

============================= 27 passed in ~2.0s ==============================
```

---

## 9. Responsible Web Scraping Safeguards

MarketLens adheres strictly to ethical data harvesting principles:
1. **Robots Exclusion Standard (`robots.txt`):** Automatically checks `robots.txt` before crawling any domain. If a target path is disallowed, the crawler logs the restriction and skips the URL.
2. **Server Respect & Pacing:** Default request pacing is enforced via `time.sleep(delay)` to prevent overloading target servers.
3. **No Circumvention Policy:** MarketLens explicitly does **NOT** attempt to bypass CAPTCHAs, spoof IP addresses, crack login credentials, or defeat anti-bot systems (e.g., Cloudflare, Datadome). If a security barrier is detected, execution halts and the barrier is reported.
4. **Data Minimization & PII Protection:** The scraper collects only public commercial listing attributes and runs an automated PII detector to prevent the inadvertent capture of personal emails or phone numbers.
5. **API Preference:** In production contexts, licensed REST APIs or bulk data feeds are always prioritized over web scraping where available.

---

## 10. Known Limitations & Future Improvements

### Current Limitations
- **JavaScript Rendering:** MarketLens parses server-side rendered HTML using `requests` and `BeautifulSoup`. Single Page Applications (SPAs) heavily dependent on client-side React/Vue rendering require pre-rendered HTML or headless browser adapters (e.g., Playwright).
- **In-Memory Deduplication:** Current duplicate tracking uses in-memory sets, which is optimal for catalogs up to ~250,000 records. Datasets with millions of records would benefit from a persistent SQLite or Redis hash store.

### Planned Improvements
- **Headless Browser Adapter:** Add a Playwright-based adapter for dynamic, JavaScript-rendered web applications.
- **Database Loader (PostgreSQL / SQLite):** Add an automated database exporter alongside CSV and Excel.
- **Asynchronous Concurrent Fetching:** Integrate `asyncio` and `aiohttp` with token bucket rate-limiters for high-throughput authorized data collections.
- **Automated Email / Slack Notification:** Alert analysts when competitor prices drop below configured thresholds.

---

## 11. Author & Contact

* **Developer:** Ankit Kumar
* **GitHub:** [@ankittdevlab](https://github.com/ankittdevlab)
* **Project Repository:** [marketlens-python-web-scraper](https://github.com/ankittdevlab/marketlens-python-web-scraper)
* **Target Role:** Research Data Analyst (Web Data and Automation)
