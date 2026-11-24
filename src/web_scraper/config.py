"""Configurações do web scraper."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_BASE_URL = "https://books.toscrape.com/"
DEFAULT_USER_AGENT = (
    "EducationalWebScraper/0.1 (+https://github.com/rodrigokk1975/web-scraper)"
)


@dataclass(frozen=True)
class ScraperConfig:
    """Parâmetros de execução do scraper."""

    base_url: str = DEFAULT_BASE_URL
    user_agent: str = DEFAULT_USER_AGENT
    timeout_seconds: float = 15.0
    delay_seconds: float = 0.5
    max_retries: int = 3
    max_pages: int = 5

    def __post_init__(self) -> None:
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url deve começar com http:// ou https://")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds deve ser maior que zero")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds não pode ser negativo")
        if self.max_retries < 0:
            raise ValueError("max_retries não pode ser negativo")
        if self.max_pages < 0:
            raise ValueError("max_pages não pode ser negativo (use 0 para ilimitado)")
