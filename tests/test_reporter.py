"""Testes unitários para o gerador de relatório analítico."""

from __future__ import annotations

import csv
from pathlib import Path

from web_scraper.models import CleanBook
from web_scraper.reporter import (
    build_summary_metrics,
    export_summary_csv,
    format_cli_summary,
)


def test_build_summary_metrics_calculates_statistics() -> None:
    books = [
        CleanBook("A", 10.0, 5, True, "https://x/1", "2026-11-24T12:00:00Z"),
        CleanBook("B", 20.0, 3, True, "https://x/2", "2026-11-24T12:00:00Z"),
        CleanBook("C", 60.0, 5, False, "https://x/3", "2026-11-24T12:00:00Z"),
    ]

    metrics = build_summary_metrics(books)

    assert metrics.total_books == 3
    assert metrics.in_stock_count == 2
    assert metrics.out_of_stock_count == 1
    assert metrics.avg_price_gbp == 30.0
    assert metrics.median_price_gbp == 20.0
    assert metrics.min_price_gbp == 10.0
    assert metrics.max_price_gbp == 60.0
    assert metrics.rating_distribution == {1: 0, 2: 0, 3: 1, 4: 0, 5: 2}


def test_build_summary_metrics_handles_empty_list() -> None:
    metrics = build_summary_metrics([])

    assert metrics.total_books == 0
    assert metrics.avg_price_gbp == 0.0
    assert metrics.rating_distribution == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}


def test_export_summary_csv_and_cli_format(tmp_path: Path) -> None:
    books = [
        CleanBook("A", 12.5, 4, True, "https://x/1", "2026-11-24T12:00:00Z"),
    ]
    metrics = build_summary_metrics(books)
    summary_file = tmp_path / "books_summary.csv"

    export_summary_csv(metrics, summary_file)

    with summary_file.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = dict(csv.reader(handle))

    assert rows["total_books"] == "1"
    assert rows["avg_price_gbp"] == "12.50"
    assert rows["rating_4_star_count"] == "1"

    text = format_cli_summary(metrics)
    assert "Total de livros:   1" in text
    assert "£12.50" in text
