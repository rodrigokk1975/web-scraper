"""Testes unitários para limpeza, normalização e deduplicação de dados."""

from __future__ import annotations

import pytest

from web_scraper.cleaner import (
    clean_books,
    clean_title,
    parse_availability,
    parse_price,
    parse_rating,
)
from web_scraper.models import RawBook


def test_clean_title_strips_extra_whitespace() -> None:
    assert clean_title("  A   Light\tin the\nAttic  ") == "A Light in the Attic"


def test_clean_title_rejects_empty() -> None:
    with pytest.raises(ValueError):
        clean_title("   \n\t ")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("£51.77", 51.77),
        ("Â£53.74", 53.74),
        (" £ 12.5 ", 12.5),
        ("£1,234.56", 1234.56),
    ],
)
def test_parse_price_valid_formats(raw: str, expected: float) -> None:
    assert parse_price(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "free", "-£10.00"])
def test_parse_price_invalid_formats(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_price(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("One", 1), ("two", 2), ("Three", 3), ("FOUR", 4), ("Five", 5)],
)
def test_parse_rating_valid(raw: str, expected: int) -> None:
    assert parse_rating(raw) == expected


def test_parse_rating_invalid() -> None:
    with pytest.raises(ValueError):
        parse_rating("Six")


def test_parse_availability() -> None:
    assert parse_availability("  In stock  ") is True
    assert parse_availability("Out of stock") is False


def test_clean_books_deduplicates_and_discards_invalid() -> None:
    raw_books = [
        RawBook(
            title="  Book A  ",
            price="£20.00",
            rating="Four",
            availability="In stock",
            url="https://books.toscrape.com/catalogue/a/index.html",
        ),
        RawBook(
            title="Book A Duplicate",
            price="£20.00",
            rating="Four",
            availability="In stock",
            url="https://books.toscrape.com/catalogue/a/index.html",
        ),
        RawBook(
            title="Book Invalid Price",
            price="N/A",
            rating="Three",
            availability="In stock",
            url="https://books.toscrape.com/catalogue/b/index.html",
        ),
        RawBook(
            title="   ",
            price="£15.00",
            rating="Two",
            availability="In stock",
            url="https://books.toscrape.com/catalogue/c/index.html",
        ),
        RawBook(
            title="Book Valid B",
            price="Â£9.99",
            rating="Five",
            availability="Out of stock",
            url="https://books.toscrape.com/catalogue/d/index.html",
        ),
    ]

    result = clean_books(raw_books, scraped_at="2026-11-24T12:00:00Z")

    assert len(result) == 2
    assert result[0].title == "Book A"
    assert result[0].price_gbp == 20.0
    assert result[0].rating == 4
    assert result[0].in_stock is True
    assert result[0].scraped_at == "2026-11-24T12:00:00Z"

    assert result[1].title == "Book Valid B"
    assert result[1].price_gbp == 9.99
    assert result[1].rating == 5
    assert result[1].in_stock is False
