"""Limpeza, normalização, validação e deduplicação de registros coletados."""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime, timezone

from web_scraper.models import CleanBook, RawBook

logger = logging.getLogger(__name__)

RATING_MAP: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}

_PRICE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")


def clean_title(raw_title: str) -> str:
    """Normaliza espaços e caracteres Unicode do título."""
    normalized = unicodedata.normalize("NFKC", raw_title)
    cleaned = " ".join(normalized.split())
    if not cleaned:
        raise ValueError("Título vazio após normalização.")
    return cleaned


def parse_price(raw_price: str) -> float:
    """Extrai o valor numérico em libras (GBP), tolerando artefatos como 'Â£'."""
    if not raw_price or not raw_price.strip():
        raise ValueError("Preço vazio.")

    sanitized = raw_price.replace(",", "").strip()
    if "-" in sanitized:
        raise ValueError(f"Preço negativo não permitido: {raw_price!r}")

    match = _PRICE_PATTERN.search(sanitized)
    if not match:
        raise ValueError(f"Não foi possível interpretar o preço: {raw_price!r}")

    value = round(float(match.group(1)), 2)
    return value


def parse_rating(raw_rating: str) -> int:
    """Converte a avaliação textual ('One'..'Five') em inteiro (1..5)."""
    key = raw_rating.strip().lower()
    if key not in RATING_MAP:
        raise ValueError(f"Avaliação inválida: {raw_rating!r}")
    return RATING_MAP[key]


def parse_availability(raw_availability: str) -> bool:
    """Converte o texto de disponibilidade em booleano."""
    return "in stock" in raw_availability.strip().lower()


def clean_books(
    raw_books: list[RawBook],
    scraped_at: str | None = None,
) -> list[CleanBook]:
    """Limpa, valida e remove duplicatas (por URL) de uma lista de RawBook."""
    timestamp = scraped_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cleaned: list[CleanBook] = []
    seen_urls: set[str] = set()
    discarded = 0
    duplicates = 0

    for raw in raw_books:
        url = raw.url.strip()
        if not url:
            discarded += 1
            logger.warning("Registro descartado por URL vazia: %r", raw.title)
            continue

        if url in seen_urls:
            duplicates += 1
            continue

        try:
            book = CleanBook(
                title=clean_title(raw.title),
                price_gbp=parse_price(raw.price),
                rating=parse_rating(raw.rating),
                in_stock=parse_availability(raw.availability),
                url=url,
                scraped_at=timestamp,
            )
        except ValueError as exc:
            discarded += 1
            logger.warning("Registro inválido descartado (%s): %s", url, exc)
            continue

        seen_urls.add(url)
        cleaned.append(book)

    logger.info(
        "Limpeza concluída: %d válidos, %d duplicados removidos, %d inválidos descartados.",
        len(cleaned),
        duplicates,
        discarded,
    )
    return cleaned
