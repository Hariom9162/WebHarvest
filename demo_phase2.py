"""MarketLens - Phase 2 Demonstration & Hands-On Exercises.

This script demonstrates:
1. Sending an HTTP GET request with requests and inspecting status codes & headers.
2. Passing raw HTML into BeautifulSoup to create a searchable parse tree.
3. Using CSS selectors to isolate elements, text, and attributes.
4. Extracting key data points from a single sample item safely.
"""

from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup


def run_phase2_demo() -> None:
    print("=" * 65)
    print("MarketLens: Phase 2 - HTTP, HTML, and BeautifulSoup Exploration")
    print("=" * 65)

    base_url = "https://books.toscrape.com/"
    
    # -------------------------------------------------------------
    # Step 1: Sending an HTTP GET request with a polite User-Agent
    # -------------------------------------------------------------
    headers = {
        "User-Agent": "MarketLens-ResearchBot/1.0 (+http://localhost/contact)"
    }
    print(f"\n[1] Sending HTTP GET request to: {base_url}")
    
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return

    # -------------------------------------------------------------
    # Step 2: Inspecting HTTP Response properties
    # -------------------------------------------------------------
    print(f"    -> Status Code : {response.status_code} ({'OK / Success' if response.status_code == 200 else 'Notice'})")
    print(f"    -> Content-Type: {response.headers.get('Content-Type')}")
    print(f"    -> Encoding    : {response.encoding}")
    print(f"    -> HTML Size   : {len(response.text):,} characters")

    # -------------------------------------------------------------
    # Step 3: Parsing HTML with BeautifulSoup
    # -------------------------------------------------------------
    print("\n[2] Parsing HTML string into BeautifulSoup parse tree...")
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Finding the page title
    page_title = soup.title.string.strip() if soup.title else "No Title"
    print(f"    -> Page Title Found: '{page_title}'")

    # -------------------------------------------------------------
    # Step 4: Locating Items with CSS Selectors
    # -------------------------------------------------------------
    # Each book on this site is contained inside an <article class="product_pod">
    book_pods = soup.select("article.product_pod")
    print(f"\n[3] Locating Product Cards with CSS Selector 'article.product_pod'")
    print(f"    -> Total books found on this page: {len(book_pods)}")

    # -------------------------------------------------------------
    # Step 5: Extracting Fields from the First Book Card
    # -------------------------------------------------------------
    print("\n[4] Extracting Sample Fields from the First Book Item:")
    first_book = book_pods[0]

    # Field 1: Title (The text is truncated 'A Light in the...', but the 'title' attribute has the full name!)
    title_element = first_book.select_one("h3 a")
    full_title = title_element.get("title") if title_element else "N/A"
    print(f"    * Full Title       : {full_title}")

    # Field 2: Price text
    price_element = first_book.select_one("p.price_color")
    raw_price = price_element.get_text(strip=True) if price_element else "N/A"
    print(f"    * Raw Price        : {raw_price}")

    # Field 3: Availability
    stock_element = first_book.select_one("p.instock.availability")
    raw_availability = stock_element.get_text(strip=True) if stock_element else "N/A"
    print(f"    * Availability     : {raw_availability}")

    # Field 4: Rating (Stored as a CSS class like ['star-rating', 'Three'])
    rating_element = first_book.select_one("p.star-rating")
    rating_classes = rating_element.get("class", []) if rating_element else []
    # Filter out the generic 'star-rating' class to get the word (e.g., 'Three')
    rating_words = [c for c in rating_classes if c != "star-rating"]
    rating_str = rating_words[0] if rating_words else "Unknown"
    print(f"    * Star Rating      : {rating_str}")

    # Field 5: Product URL (Relative path converted to absolute URL)
    relative_url = title_element.get("href") if title_element else ""
    full_product_url = urljoin(base_url, relative_url)
    print(f"    * Product Page URL : {full_product_url}")

    print("\n" + "=" * 65)
    print("Phase 2 Demo Finished Successfully!")
    print("=" * 65)


if __name__ == "__main__":
    run_phase2_demo()
