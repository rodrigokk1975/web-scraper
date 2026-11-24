"""Testes unitários para ordenação e exportação CSV."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from web_scraper.exporter import CSV_FIELDNAMES, export_books_csv, sort_books
from web_scraper.models import CleanBook


def _sample_books() -> list[CleanBook]:
    return [
        CleanBook(
            title="Zebra Book",
            price_gbp=30.0,
            rating=3,
            in_stock=True,
            url="https://books.toscrape.com/z",
            scraped_at="2026-11-24T12:00:00Z",
        ),
        CleanBook(
            title="Alpha Book",
            price_gbp=15.5,
            rating=5,
            in_stock=True,
            url="https://books.toscrape.com/a",
            scraped_at="2026-11-24T12:00:00Z",
        ),
        CleanBook(
            title="Beta Book",
            price_gbp=10.0,
            rating=5,
            in_stock=False,
            url="https://books.toscrape.com/b",
            scraped_at="2026-11-24T12:00:00Z",
        ),
    ]


def test_sort_books_by_rating_desc_breaks_ties_by_price_asc() -> None:
    ordered = sort_books(_sample_books(), sort_by="rating_desc")
    assert [b.title for b in ordered] == ["Beta Book", "Alpha Book", "Zebra Book"]


def test_sort_books_by_price_and_title() -> None:
    books = _sample_books()
    assert [b.title for b in sort_books(books, "price_asc")] == [
        "Beta Book",
        "Alpha Book",
        "Zebra Book",
    ]
    assert [b.title for b in sort_books(books, "price_desc")] == [
        "Zebra Book",
        "Alpha Book",
        "Beta Book",
    ]
    assert [b.title for b in sort_books(books, "title_asc")] == [
        "Alpha Book",
        "Beta Book",
        "Zebra Book",
    ]


def test_sort_books_rejects_invalid_option() -> None:
    with pytest.raises(ValueError):
        sort_books(_sample_books(), sort_by="unknown")  # type: ignore[arg-type]


def test_export_books_csv_writes_expected_headers_and_rows(tmp_path: Path) -> None:
    output_file = tmp_path / "nested" / "books_clean.csv"
    books = sort_books(_sample_books(), "rating_desc")

    export_books_csv(books, output_file)

    assert output_file.exists()
    with output_file.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == CSV_FIELDNAMES
        rows = list(reader)

    assert len(rows) == 3
    assert rows[0]["title"] == "Beta Book"
    assert rows[0]["price_gbp"] == "10.00"
    assert rows[0]["rating"] == "5"
    assert rows[0]["in_stock"] == "False"
