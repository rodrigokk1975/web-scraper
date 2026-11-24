"""Testes de integração da CLI e do pipeline ponta a ponta."""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import MagicMock

from web_scraper.cli import build_parser, main, run_pipeline
from web_scraper.config import ScraperConfig
from web_scraper.robots import RobotsChecker

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "catalogue_page.html"


def test_cli_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.max_pages == 5
    assert args.delay == 0.5
    assert args.output_dir == Path("output")
    assert args.sort == "rating_desc"
    assert args.verbose is False


def test_run_pipeline_generates_clean_and_summary_csvs(tmp_path: Path) -> None:
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    mock_client = MagicMock()
    mock_client.get_text.return_value = html

    robots = RobotsChecker("https://books.toscrape.com/", "TestAgent")
    robots.load_from_text("User-agent: *\nAllow: /\n")

    config = ScraperConfig(max_pages=1, delay_seconds=0.0)
    clean_csv, summary_csv, summary_text = run_pipeline(
        config=config,
        output_dir=tmp_path,
        sort_by="rating_desc",
        client=mock_client,
        robots_checker=robots,
    )

    assert clean_csv.exists()
    assert summary_csv.exists()
    assert "Total de livros:   2" in summary_text

    with clean_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert rows[0]["title"] == "Tipping the Velvet"
    assert rows[0]["price_gbp"] == "53.74"
    assert rows[0]["rating"] == "5"
    assert rows[1]["title"] == "A Light in the Attic"


def test_main_returns_nonzero_on_invalid_config() -> None:
    exit_code = main(["--max-pages", "-3"])
    assert exit_code == 1
