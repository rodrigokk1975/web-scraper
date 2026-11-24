"""Modelos de dados brutos e limpos do scraper."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RawBook:
    """Representação bruta de um livro extraído diretamente do HTML."""

    title: str
    price: str
    rating: str
    availability: str
    url: str


@dataclass(frozen=True)
class CleanBook:
    """Representação limpa, validada e padronizada pronta para exportação."""

    title: str
    price_gbp: float
    rating: int
    in_stock: bool
    url: str
    scraped_at: str

    def to_dict(self) -> dict[str, object]:
        """Converte o livro limpo em dicionário para escrita em CSV."""
        return asdict(self)
