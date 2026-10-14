"""MarketLens - Multi-Page Web Scraper with Pagination.

Extracts structured book data across multiple pages from https://books.toscrape.com/
and saves all raw collected records to data/raw/books_raw.csv.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin
import csv
import sys
import time
import requests
from bs4 import BeautifulSoup


# Configuration Defaults
TARGET_URL = "https://books.toscrape.com/"
DEFAULT_MAX_PAGES = 3
DEFAULT_DELAY_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 10
USER_AGENT = "MarketLens-ResearchBot/1.0 (+http://localhost/contact)"
OUTPUT_FILE_PATH = Path("data") / "raw" / "books_raw.csv"


def fetch_page_html(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Optional[str]:
    """Fetch HTML content from a URL safely with timeouts and polite headers.
    
    Args:
        url: The web page address to request.
        timeout: Maximum seconds to wait before raising a Timeout exception.
        
    Returns:
        The decoded HTML string if successful, or None if a network error occurs.
    """
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Ensure correct UTF-8 encoding so currency symbols (£) aren't garbled
        if response.encoding.lower() in ("iso-8859-1", "ascii"):
            response.encoding = response.apparent_encoding or "utf-8"
            
        return response.text
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timed out while connecting to: {url}", file=sys.stderr)
        return None
    except requests.exceptions.HTTPError as err:
        print(f"[ERROR] HTTP error {response.status_code} occurred for: {url} -> {err}", file=sys.stderr)
        return None
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Network connection failed for: {url} -> {err}", file=sys.stderr)
        return None


def extract_book_record(card: BeautifulSoup, source_url: str) -> Dict[str, Any]:
    """Extract individual data fields from a single book HTML card element safely.
    
    Args:
        card: BeautifulSoup tag corresponding to an <article class="product_pod">.
        source_url: The URL of the page where this card was found.
        
    Returns:
        A dictionary containing the extracted fields.
    """
    # 1. Book Title
    title_tag = card.select_one("h3 a")
    title = title_tag.get("title") if title_tag else None
    if not title and title_tag:
        title = title_tag.get_text(strip=True)

    # 2. Price
    price_tag = card.select_one("p.price_color")
    price = price_tag.get_text(strip=True) if price_tag else ""

    # 3. Availability
    stock_tag = card.select_one("p.instock.availability")
    availability = stock_tag.get_text(strip=True) if stock_tag else ""

    # 4. Product Page URL
    relative_href = title_tag.get("href") if title_tag else ""
    product_url = urljoin(source_url, relative_href) if relative_href else ""

    # 5. Rating
    rating_tag = card.select_one("p.star-rating")
    rating_classes = rating_tag.get("class", []) if rating_tag else []
    rating_words = [cls_name for cls_name in rating_classes if cls_name != "star-rating"]
    rating = rating_words[0] if rating_words else "Not Rated"

    # 6. Extraction Metadata
    extraction_timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "title": title,
        "price": price,
        "availability": availability,
        "product_url": product_url,
        "rating": rating,
        "source_url": source_url,
        "extraction_timestamp": extraction_timestamp,
    }


def parse_books_from_html(html_text: str, source_url: str) -> List[Dict[str, Any]]:
    """Parse HTML string and extract a list of book records.
    
    Args:
        html_text: Raw HTML string returned from requests.
        source_url: The source URL of the page.
        
    Returns:
        List of extracted book dictionary records.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    book_cards = soup.select("article.product_pod")
    
    records: List[Dict[str, Any]] = []
    for card in book_cards:
        record = extract_book_record(card, source_url)
        records.append(record)
        
    return records


def find_next_page_url(soup: BeautifulSoup, current_page_url: str) -> Optional[str]:
    """Find the URL for the next page from the pagination control.
    
    On books.toscrape.com, the pager is structured as:
    <ul class="pager">
        <li class="next"><a href="catalogue/page-2.html">next</a></li>
    </ul>
    
    Args:
        soup: BeautifulSoup parse tree of the current page.
        current_page_url: URL of the current page (to resolve relative links).
        
    Returns:
        The absolute URL of the next page, or None if no next page exists.
    """
    next_button = soup.select_one("li.next a")
    if not next_button:
        return None

    relative_next_href = next_button.get("href")
    if not relative_next_href:
        return None

    # Resolve relative link with respect to current page URL
    return urljoin(current_page_url, relative_next_href)


def scrape_multiple_pages(
    start_url: str = TARGET_URL,
    max_pages: int = DEFAULT_MAX_PAGES,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
) -> List[Dict[str, Any]]:
    """Scrape records across multiple paginated pages.
    
    Guarantees:
    - Never revisits the same URL (loop prevention).
    - Stops when page limit is reached or when there are no more pages.
    - Pauses between requests to respect server bandwidth.
    - Preserves previously collected data if a network error occurs.
    
    Args:
        start_url: Entry point URL.
        max_pages: Maximum number of pages to crawl.
        delay_seconds: Polite pause between HTTP requests.
        
    Returns:
        Combined list of all extracted records across all processed pages.
    """
    all_records: List[Dict[str, Any]] = []
    visited_urls: Set[str] = set()
    current_url: Optional[str] = start_url
    pages_processed = 0

    print(f"[START] Beginning multi-page scrape (Max pages: {max_pages}, Delay: {delay_seconds}s)")

    while current_url and pages_processed < max_pages:
        # Loop prevention check
        if current_url in visited_urls:
            print(f"[WARNING] Detected loop! Already visited: {current_url}. Stopping pagination.")
            break

        pages_processed += 1
        print(f"\n--- [Page {pages_processed}/{max_pages}] Fetching: {current_url} ---")
        visited_urls.add(current_url)

        # 1. Fetch
        html = fetch_page_html(current_url)
        if not html:
            print(f"[ERROR] Failed to fetch {current_url}. Halting further navigation, preserving current records.", file=sys.stderr)
            break

        # 2. Parse
        soup = BeautifulSoup(html, "html.parser")
        page_records = parse_books_from_html(html, current_url)
        all_records.extend(page_records)
        print(f"[INFO] Extracted {len(page_records)} books from this page. Total so far: {len(all_records)}")

        # 3. Detect Next Page
        next_url = find_next_page_url(soup, current_url)
        if next_url:
            current_url = next_url
            # Polite delay before next page request (only if more pages remain)
            if pages_processed < max_pages:
                print(f"[WAIT] Sleeping {delay_seconds} second(s) before next request...")
                time.sleep(delay_seconds)
        else:
            print("[INFO] No 'next' button found. Reached the final page.")
            current_url = None

    print(f"\n[FINISH] Multi-page scraping complete.")
    print(f"[SUMMARY] Total pages processed: {pages_processed}")
    print(f"[SUMMARY] Total records collected: {len(all_records)}")
    return all_records


def save_records_to_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Save records to a CSV file with proper UTF-8 encoding and headers.
    
    Args:
        records: List of dictionary records to write.
        output_path: Destination file path.
    """
    if not records:
        print("[WARNING] No records to save.", file=sys.stderr)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "title",
        "price",
        "availability",
        "product_url",
        "rating",
        "source_url",
        "extraction_timestamp",
    ]

    with open(output_path, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"[SUCCESS] Saved {len(records)} records to: {output_path}")


def main() -> None:
    """Entry point for running multi-page scraping."""
    # Allow user to specify page count via command line: python scraper.py [num_pages]
    max_pages = DEFAULT_MAX_PAGES
    if len(sys.argv) > 1:
        try:
            max_pages = int(sys.argv[1])
            if max_pages <= 0:
                raise ValueError
        except ValueError:
            print(f"[WARNING] Invalid page argument '{sys.argv[1]}'. Using default ({DEFAULT_MAX_PAGES}).")
            max_pages = DEFAULT_MAX_PAGES

    print("=" * 65)
    print("MarketLens: Phase 4 - Multi-Page Web Scraping")
    print("=" * 65)

    records = scrape_multiple_pages(start_url=TARGET_URL, max_pages=max_pages, delay_seconds=DEFAULT_DELAY_SECONDS)
    save_records_to_csv(records, OUTPUT_FILE_PATH)
    print("=" * 65)


if __name__ == "__main__":
    main()
