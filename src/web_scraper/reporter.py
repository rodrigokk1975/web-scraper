"""Geração de métricas agregadas e relatório resumo em CSV e texto."""

from __future__ import annotations

import csv
import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

from web_scraper.models import CleanBook

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SummaryMetrics:
    """Métricas analíticas consolidadas dos livros coletados."""

    total_books: int
    in_stock_count: int
    out_of_stock_count: int
    avg_price_gbp: float
    median_price_gbp: float
    min_price_gbp: float
    max_price_gbp: float
    rating_distribution: dict[int, int]


def build_summary_metrics(books: list[CleanBook]) -> SummaryMetrics:
    """Calcula métricas estatísticas e distribuição de avaliações."""
    counts = Counter(book.rating for book in books)
    rating_dist = {stars: counts.get(stars, 0) for stars in range(1, 6)}

    if not books:
        return SummaryMetrics(
            total_books=0,
            in_stock_count=0,
            out_of_stock_count=0,
            avg_price_gbp=0.0,
            median_price_gbp=0.0,
            min_price_gbp=0.0,
            max_price_gbp=0.0,
            rating_distribution=rating_dist,
        )

    prices = [book.price_gbp for book in books]
    in_stock_count = sum(1 for book in books if book.in_stock)

    return SummaryMetrics(
        total_books=len(books),
        in_stock_count=in_stock_count,
        out_of_stock_count=len(books) - in_stock_count,
        avg_price_gbp=round(mean(prices), 2),
        median_price_gbp=round(median(prices), 2),
        min_price_gbp=round(min(prices), 2),
        max_price_gbp=round(max(prices), 2),
        rating_distribution=rating_dist,
    )


def export_summary_csv(metrics: SummaryMetrics, filepath: Path) -> Path:
    """Exporta as métricas consolidadas em um CSV chave-valor."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    rows: list[tuple[str, object]] = [
        ("total_books", metrics.total_books),
        ("in_stock_count", metrics.in_stock_count),
        ("out_of_stock_count", metrics.out_of_stock_count),
        ("avg_price_gbp", f"{metrics.avg_price_gbp:.2f}"),
        ("median_price_gbp", f"{metrics.median_price_gbp:.2f}"),
        ("min_price_gbp", f"{metrics.min_price_gbp:.2f}"),
        ("max_price_gbp", f"{metrics.max_price_gbp:.2f}"),
    ]
    for stars in range(1, 6):
        rows.append((f"rating_{stars}_star_count", metrics.rating_distribution.get(stars, 0)))

    with filepath.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerows(rows)

    logger.info("CSV de resumo analítico salvo em %s.", filepath)
    return filepath


def format_cli_summary(metrics: SummaryMetrics) -> str:
    """Formata um resumo executivo legível para impressão no terminal."""
    lines = [
        "=== Resumo da Coleta ===",
        f"Total de livros:   {metrics.total_books}",
        f"Em estoque:        {metrics.in_stock_count}",
        f"Sem estoque:       {metrics.out_of_stock_count}",
        f"Preço médio (GBP): £{metrics.avg_price_gbp:.2f}",
        f"Preço mediano:     £{metrics.median_price_gbp:.2f}",
        f"Faixa de preço:    £{metrics.min_price_gbp:.2f} - £{metrics.max_price_gbp:.2f}",
        "Distribuição por avaliação:",
    ]
    for stars in range(5, 0, -1):
        count = metrics.rating_distribution.get(stars, 0)
        lines.append(f"  {stars} estrela(s): {count}")
    return "\n".join(lines)
