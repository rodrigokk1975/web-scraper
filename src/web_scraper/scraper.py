"""Orquestrador de coleta paginada respeitando robots.txt e rate limiting."""

from __future__ import annotations

import logging

from web_scraper.client import PoliteHttpClient
from web_scraper.config import ScraperConfig
from web_scraper.models import RawBook
from web_scraper.parser import parse_catalogue_page
from web_scraper.robots import RobotsChecker

logger = logging.getLogger(__name__)


class RobotsDisallowedError(PermissionError):
    """Lançada quando o robots.txt proíbe a coleta da URL alvo."""


class BookScraper:
    """Coleta livros paginados a partir de uma URL inicial."""

    def __init__(
        self,
        config: ScraperConfig,
        client: PoliteHttpClient,
        robots_checker: RobotsChecker,
    ) -> None:
        self.config = config
        self.client = client
        self.robots_checker = robots_checker

    def scrape(self) -> list[RawBook]:
        """Percorre páginas do catálogo respeitando robots.txt e limite de páginas."""
        current_url: str | None = self.config.base_url
        crawl_delay = self.robots_checker.crawl_delay()
        collected: list[RawBook] = []
        visited: set[str] = set()
        pages_scraped = 0

        while current_url is not None:
            if self.config.max_pages > 0 and pages_scraped >= self.config.max_pages:
                logger.info("Limite de %d página(s) atingido.", self.config.max_pages)
                break

            if current_url in visited:
                logger.warning("Loop de paginação detectado em %s. Encerrando.", current_url)
                break

            if not self.robots_checker.can_fetch(current_url):
                raise RobotsDisallowedError(
                    f"Coleta proibida pelo robots.txt para a URL: {current_url}"
                )

            visited.add(current_url)
            pages_scraped += 1
            logger.info("Coletando página %d: %s", pages_scraped, current_url)

            html = self.client.get_text(current_url, min_delay=crawl_delay)
            page_books, next_url = parse_catalogue_page(html, current_url)
            collected.extend(page_books)
            logger.info(
                "Página %d processada: %d livros encontrados.",
                pages_scraped,
                len(page_books),
            )
            current_url = next_url

        return collected
