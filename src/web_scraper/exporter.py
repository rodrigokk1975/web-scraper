"""Ordenação e exportação dos livros limpos para CSV."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Literal

from web_scraper.models import CleanBook

logger = logging.getLogger(__name__)

SortOption = Literal["rating_desc", "price_asc", "price_desc", "title_asc"]
VALID_SORT_OPTIONS: tuple[SortOption, ...] = (
    "rating_desc",
    "price_asc",
    "price_desc",
    "title_asc",
)

CSV_FIELDNAMES: tuple[str, ...] = (
    "title",
    "price_gbp",
    "rating",
    "in_stock",
    "url",
    "scraped_at",
)


def sort_books(
    books: list[CleanBook],
    sort_by: SortOption = "rating_desc",
) -> list[CleanBook]:
    """Retorna uma nova lista de livros ordenada segundo o critério escolhido."""
    if sort_by == "rating_desc":
        return sorted(books, key=lambda b: (-b.rating, b.price_gbp, b.title.lower()))
    if sort_by == "price_asc":
        return sorted(books, key=lambda b: (b.price_gbp, -b.rating, b.title.lower()))
    if sort_by == "price_desc":
        return sorted(books, key=lambda b: (-b.price_gbp, -b.rating, b.title.lower()))
    if sort_by == "title_asc":
        return sorted(books, key=lambda b: (b.title.lower(), b.price_gbp))
    raise ValueError(f"Critério de ordenação inválido: {sort_by!r}")


def export_books_csv(books: list[CleanBook], filepath: Path) -> Path:
    """Exporta os livros limpos em CSV UTF-8 com BOM (compatível com Excel)."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for book in books:
            row = book.to_dict()
            row["price_gbp"] = f"{book.price_gbp:.2f}"
            writer.writerow(row)

    logger.info("CSV de dados limpos salvo em %s (%d registros).", filepath, len(books))
    return filepath
