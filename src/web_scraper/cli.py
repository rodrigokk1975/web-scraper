"""Interface de linha de comando (CLI) do web scraper."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

import requests

from web_scraper.cleaner import clean_books
from web_scraper.client import PoliteHttpClient
from web_scraper.config import DEFAULT_BASE_URL, ScraperConfig
from web_scraper.exporter import (
    VALID_SORT_OPTIONS,
    SortOption,
    export_books_csv,
    sort_books,
)
from web_scraper.reporter import (
    build_summary_metrics,
    export_summary_csv,
    format_cli_summary,
)
from web_scraper.robots import RobotsChecker
from web_scraper.scraper import BookScraper, RobotsDisallowedError


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        prog="web-scraper",
        description=(
            "Coleta, limpa e gera relatórios em CSV a partir de books.toscrape.com "
            "respeitando robots.txt e rate limiting."
        ),
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"URL inicial do catálogo (padrão: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Número máximo de páginas a coletar (0 para todas; padrão: 5)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Intervalo mínimo em segundos entre requisições (padrão: 0.5)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Diretório de saída para os arquivos CSV (padrão: output)",
    )
    parser.add_argument(
        "--sort",
        choices=VALID_SORT_OPTIONS,
        default="rating_desc",
        help="Critério de ordenação do CSV principal (padrão: rating_desc)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Ativa logs detalhados (DEBUG)",
    )
    return parser


def configure_logging(verbose: bool = False) -> None:
    """Configura o formato e o nível global de logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )


def run_pipeline(
    config: ScraperConfig,
    output_dir: Path,
    sort_by: SortOption = "rating_desc",
    client: PoliteHttpClient | None = None,
    robots_checker: RobotsChecker | None = None,
) -> tuple[Path, Path, str]:
    """Executa o fluxo completo: coleta -> limpeza -> ordenação -> exportação CSV."""
    owns_client = client is None
    active_client = client or PoliteHttpClient(config)
    active_robots = robots_checker or RobotsChecker(
        base_url=config.base_url,
        user_agent=config.user_agent,
        timeout_seconds=config.timeout_seconds,
        session=active_client.session,
    )

    try:
        scraper = BookScraper(
            config=config,
            client=active_client,
            robots_checker=active_robots,
        )
        raw_books = scraper.scrape()
    finally:
        if owns_client:
            active_client.close()

    cleaned_books = clean_books(raw_books)
    ordered_books = sort_books(cleaned_books, sort_by=sort_by)
    metrics = build_summary_metrics(ordered_books)

    clean_csv = export_books_csv(ordered_books, output_dir / "books_clean.csv")
    summary_csv = export_summary_csv(metrics, output_dir / "books_summary.csv")
    summary_text = format_cli_summary(metrics)
    return clean_csv, summary_csv, summary_text


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada da CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    try:
        config = ScraperConfig(
            base_url=args.base_url,
            delay_seconds=args.delay,
            max_pages=args.max_pages,
        )
        clean_csv, summary_csv, summary_text = run_pipeline(
            config=config,
            output_dir=args.output_dir,
            sort_by=args.sort,
        )
    except (ValueError, RobotsDisallowedError, requests.RequestException) as exc:
        logging.getLogger(__name__).error("Execução interrompida: %s", exc)
        return 1

    print()
    print(summary_text)
    print(f"\nArquivos gerados:\n  - {clean_csv}\n  - {summary_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
