"""Testes unitários para o parser HTML e o coletor paginado."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from web_scraper.config import ScraperConfig
from web_scraper.parser import parse_catalogue_page
from web_scraper.robots import RobotsChecker
from web_scraper.scraper import BookScraper, RobotsDisallowedError

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "catalogue_page.html"


def test_parse_catalogue_page_extracts_books_and_next_url() -> None:
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    books, next_url = parse_catalogue_page(html, "https://books.toscrape.com/")

    assert len(books) == 2
    assert books[0].title == "A Light in the Attic"
    assert books[0].price == "£51.77"
    assert books[0].rating == "Three"
    assert books[0].availability == "In stock"
    assert (
        books[0].url
        == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )

    assert books[1].title == "Tipping the Velvet"
    assert books[1].rating == "Five"
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_parse_catalogue_page_without_next_link() -> None:
    html = """
    <article class="product_pod">
      <p class="star-rating One"></p>
      <h3><a href="book-1/index.html" title="Solo Book">Solo</a></h3>
      <p class="price_color">£10.00</p>
      <p class="instock availability">In stock</p>
    </article>
    """
    books, next_url = parse_catalogue_page(
        html, "https://books.toscrape.com/catalogue/page-50.html"
    )

    assert len(books) == 1
    assert books[0].url == "https://books.toscrape.com/catalogue/book-1/index.html"
    assert next_url is None


def test_book_scraper_respects_max_pages() -> None:
    page1_html = FIXTURE_PATH.read_text(encoding="utf-8")
    page2_html = page1_html.replace("catalogue/page-2.html", "page-3.html")

    mock_client = MagicMock()
    mock_client.get_text.side_effect = [page1_html, page2_html]

    robots = RobotsChecker("https://books.toscrape.com/", "TestAgent")
    robots.load_from_text("User-agent: *\nAllow: /\n")

    scraper = BookScraper(
        config=ScraperConfig(max_pages=2),
        client=mock_client,
        robots_checker=robots,
    )

    books = scraper.scrape()
    assert len(books) == 4
    assert mock_client.get_text.call_count == 2


def test_book_scraper_aborts_when_robots_disallows() -> None:
    mock_client = MagicMock()
    robots = RobotsChecker("https://books.toscrape.com/", "TestAgent")
    robots.load_from_text("User-agent: *\nDisallow: /\n")

    scraper = BookScraper(
        config=ScraperConfig(max_pages=1),
        client=mock_client,
        robots_checker=robots,
    )

    with pytest.raises(RobotsDisallowedError):
        scraper.scrape()
    mock_client.get_text.assert_not_called()
