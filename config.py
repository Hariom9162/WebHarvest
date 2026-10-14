"""MarketLens - Configuration & Centralized Logging System.

Manages application settings, environment variables, directories,
and configures dual-target logging (detailed file logging + clean terminal logging).
"""

from pathlib import Path
import logging
import os
import sys
from dotenv import load_dotenv

# Load variables from .env file if it exists
load_dotenv()

# Project Root Directory
PROJECT_ROOT = Path(__file__).resolve().parent

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DATA_DIR = DATA_DIR / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure runtime directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Application Settings with Defaults
BASE_URL = os.getenv("SCRAPER_BASE_URL", "https://books.toscrape.com/")
DEFAULT_MAX_PAGES = int(os.getenv("SCRAPER_MAX_PAGES", "3"))
DEFAULT_REQUEST_DELAY = float(os.getenv("SCRAPER_REQUEST_DELAY_SECONDS", "1.0"))
DEFAULT_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "10"))
USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "MarketLensBot/1.0 (+http://localhost/research-contact)"
)
LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()

# Default Output File Paths
RAW_CSV_PATH = RAW_DATA_DIR / "books_raw.csv"
CLEANED_CSV_PATH = PROCESSED_DATA_DIR / "books_cleaned.csv"
CLEANED_XLSX_PATH = PROCESSED_DATA_DIR / "books_cleaned.xlsx"
REJECTED_CSV_PATH = PROCESSED_DATA_DIR / "rejected_records.csv"
REPORT_TXT_PATH = REPORTS_DATA_DIR / "market_summary_report.txt"
REPORT_CHART_PATH = REPORTS_DATA_DIR / "market_analytics_chart.png"
REPORT_RATING_CSV_PATH = REPORTS_DATA_DIR / "rating_distribution.csv"
LOG_FILE_PATH = LOGS_DIR / "marketlens.log"


def setup_logging(
    log_file: Path = LOG_FILE_PATH,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    """Configure dual-destination logging:
    
    1. Terminal/Console: Concise messages (e.g. "[INFO] Scraped 20 items")
    2. File: Comprehensive timestamped audit log with module names and line numbers.
    
    Args:
        log_file: Path to the log file.
        console_level: Minimum severity level to show in terminal.
        file_level: Minimum severity level to save in the file.
        
    Returns:
        Root logger for marketlens.
    """
    logger = logging.getLogger("marketlens")
    logger.setLevel(logging.DEBUG)  # Capture everything; handlers filter individually

    # Avoid duplicate handlers if setup_logging is called multiple times
    if logger.handlers:
        return logger

    # 1. Console Handler (User-facing, concise format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        "[%(levelname)s] %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (Deep auditing, includes timestamps and source line)
    # Use utf-8 encoding so currency symbols (£) don't crash Windows logging
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
