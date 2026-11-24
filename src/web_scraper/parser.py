"""Parser HTML com BeautifulSoup para páginas de catálogo do books.toscrape.com."""

from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from web_scraper.models import RawBook


def _extract_rating_token(classes: list[str]) -> str:
    """Extrai o token de avaliação (One..Five) das classes CSS de p.star-rating."""
    for cls in classes:
        if cls != "star-rating":
            return cls
    return ""


def parse_catalogue_page(html: str, page_url: str) -> tuple[list[RawBook], str | None]:
    """Extrai livros brutos e o link da próxima página de uma página de catálogo."""
    soup = BeautifulSoup(html, "html.parser")
    books: list[RawBook] = []

    for article in soup.select("article.product_pod"):
        link_tag = article.select_one("h3 > a")
        if link_tag is None:
            continue

        title = str(link_tag.get("title") or link_tag.get_text(strip=True))
        relative_href = str(link_tag.get("href") or "")
        absolute_url = urljoin(page_url, relative_href) if relative_href else ""

        price_tag = article.select_one("p.price_color")
        price_text = price_tag.get_text(strip=True) if price_tag else ""

        rating_tag = article.select_one("p.star-rating")
        rating_classes = list(rating_tag.get("class", [])) if rating_tag else []
        rating_text = _extract_rating_token(rating_classes)

        avail_tag = article.select_one("p.instock.availability")
        availability_text = avail_tag.get_text(" ", strip=True) if avail_tag else ""

        books.append(
            RawBook(
                title=title,
                price=price_text,
                rating=rating_text,
                availability=availability_text,
                url=absolute_url,
            )
        )

    next_link = soup.select_one("li.next > a")
    next_url: str | None = None
    if next_link and next_link.get("href"):
        next_url = urljoin(page_url, str(next_link["href"]))

    return books, next_url
