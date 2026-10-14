"""MarketLens - Source Adapter Unit Tests.

Tests the BaseSource interface contract on BooksSource and QuotesSource adapters.
"""

import pytest
from marketlens.sources import BooksSource, QuotesSource, get_source_adapter
from marketlens.sources.base import BaseSource

SAMPLE_QUOTE_HTML = """
<div class="quote">
    <span class="text">“The only true wisdom is in knowing you know nothing.”</span>
    <span>by <small class="author">Socrates</small>
    <a href="/author/Socrates">(about)</a>
    </span>
    <div class="tags">
        <a class="tag" href="/tag/wisdom/">wisdom</a>
        <a class="tag" href="/tag/knowledge/">knowledge</a>
    </div>
</div>
<ul class="pager">
    <li class="next"><a href="/page/2/">Next</a></li>
</ul>
"""


def test_factory_get_source_adapter() -> None:
    """Test factory instantiates correct adapter subclasses."""
    books = get_source_adapter("books")
    assert isinstance(books, BooksSource)
    assert isinstance(books, BaseSource)
    assert books.source_name == "books"

    quotes = get_source_adapter("quotes")
    assert isinstance(quotes, QuotesSource)
    assert isinstance(quotes, BaseSource)
    assert quotes.source_name == "quotes"


def test_factory_invalid_source_raises_value_error() -> None:
    """Test factory raises ValueError with helpful message for unknown source."""
    with pytest.raises(ValueError, match="Unknown data source 'unsupported'"):
        get_source_adapter("unsupported")


def test_quotes_source_parsing() -> None:
    """Test QuotesSource parsing quote items, authors, and tags."""
    adapter = QuotesSource()
    records = adapter.parse_items(SAMPLE_QUOTE_HTML, "https://quotes.toscrape.com/")
    assert len(records) == 1

    quote = records[0]
    assert quote["author"] == "Socrates"
    assert quote["quote_text"] == "The only true wisdom is in knowing you know nothing."
    assert "wisdom" in quote["tags"]
    assert quote["author_url"] == "https://quotes.toscrape.com/author/Socrates"


def test_quotes_source_validation_and_cleaning() -> None:
    """Test validation and cleaning on quotes."""
    adapter = QuotesSource()

    valid_record = {
        "quote_text": "Live as if you were to die tomorrow.",
        "author": "Mahatma Gandhi",
    }
    is_valid, errors = adapter.validate_record(valid_record)
    assert is_valid is True
    assert len(errors) == 0

    invalid_record = {"quote_text": "Tiny", "author": ""}
    is_valid, errors = adapter.validate_record(invalid_record)
    assert is_valid is False
    assert len(errors) >= 1
