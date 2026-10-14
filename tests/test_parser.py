"""MarketLens - Parser Unit Tests.

Tests HTML parsing, CSS selectors, missing node fallbacks,
and pagination detection without live network dependency.
"""

import pytest
from marketlens.parser import BookParser

SAMPLE_VALID_HTML = """
<article class="product_pod">
    <h3><a href="catalogue/clean-code_1/index.html" title="Clean Code: A Handbook of Agile Software Craftsmanship">Clean Code...</a></h3>
    <p class="star-rating Four"><i class="icon-star"></i></p>
    <div class="product_price">
        <p class="price_color">£32.50</p>
        <p class="instock availability"><i class="icon-ok"></i> In stock</p>
    </div>
</article>
<ul class="pager">
    <li class="next"><a href="catalogue/page-2.html">next</a></li>
</ul>
"""

SAMPLE_MISSING_NODES_HTML = """
<article class="product_pod">
    <h3><a>Missing Title Attribute</a></h3>
    <!-- Missing star-rating -->
    <div class="product_price">
        <!-- Missing price_color -->
        <p class="instock availability">Out of stock</p>
    </div>
</article>
"""


def test_parse_valid_book_card() -> None:
    """Test extracting all fields from a complete, valid book card."""
    records = BookParser.parse_books(SAMPLE_VALID_HTML, "https://books.toscrape.com/")
    assert len(records) == 1

    book = records[0]
    assert book["title"] == "Clean Code: A Handbook of Agile Software Craftsmanship"
    assert book["price"] == "£32.50"
    assert book["availability"] == "In stock"
    assert book["rating"] == "Four"
    assert book["product_url"] == "https://books.toscrape.com/catalogue/clean-code_1/index.html"
    assert book["source_url"] == "https://books.toscrape.com/"
    assert "extraction_timestamp" in book


def test_parse_missing_elements_does_not_crash() -> None:
    """Test that cards missing price, rating, or title attribute don't crash."""
    records = BookParser.parse_books(SAMPLE_MISSING_NODES_HTML, "https://books.toscrape.com/")
    assert len(records) == 1

    book = records[0]
    assert book["title"] == "Missing Title Attribute"
    assert book["price"] == ""
    assert book["rating"] == "Not Rated"
    assert book["availability"] == "Out of stock"


def test_pagination_next_url_extracted() -> None:
    """Test that next page link is resolved to an absolute URL."""
    next_url = BookParser.extract_next_page_url(SAMPLE_VALID_HTML, "https://books.toscrape.com/")
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_pagination_returns_none_when_no_next_link() -> None:
    """Test that extract_next_page_url returns None when no pager exists."""
    html_without_pager = "<article class='product_pod'></article>"
    next_url = BookParser.extract_next_page_url(html_without_pager, "https://books.toscrape.com/")
    assert next_url is None


def test_empty_html_handling() -> None:
    """Test that empty HTML strings are handled gracefully."""
    assert BookParser.parse_books("", "https://books.toscrape.com/") == []
    assert BookParser.extract_next_page_url("", "https://books.toscrape.com/") is None
