"""Testes unitários para o cliente HTTP educado."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from web_scraper.client import PoliteHttpClient
from web_scraper.config import ScraperConfig


def test_config_validation_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        ScraperConfig(base_url="ftp://example.com")
    with pytest.raises(ValueError):
        ScraperConfig(timeout_seconds=0)
    with pytest.raises(ValueError):
        ScraperConfig(delay_seconds=-1)
    with pytest.raises(ValueError):
        ScraperConfig(max_pages=-1)


def test_client_applies_rate_limiting_between_requests() -> None:
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "<html>ok</html>"
    mock_response.encoding = "utf-8"
    mock_session.get.return_value = mock_response

    sleeps: list[float] = []
    times = iter([10.0, 10.2, 10.2])

    client = PoliteHttpClient(
        config=ScraperConfig(delay_seconds=1.0),
        session=mock_session,
        sleep_fn=sleeps.append,
        clock_fn=lambda: next(times),
    )

    assert client.get_text("https://books.toscrape.com/page-1.html") == "<html>ok</html>"
    assert client.get_text("https://books.toscrape.com/page-2.html") == "<html>ok</html>"

    assert len(sleeps) == 1
    assert sleeps[0] == pytest.approx(0.8, abs=1e-6)


def test_client_respects_higher_crawl_delay() -> None:
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "<html>ok</html>"
    mock_response.encoding = "utf-8"
    mock_session.get.return_value = mock_response

    sleeps: list[float] = []
    times = iter([1.0, 1.5, 1.5])

    client = PoliteHttpClient(
        config=ScraperConfig(delay_seconds=0.5),
        session=mock_session,
        sleep_fn=sleeps.append,
        clock_fn=lambda: next(times),
    )

    client.get_text("https://books.toscrape.com/page-1.html", min_delay=2.0)
    client.get_text("https://books.toscrape.com/page-2.html", min_delay=2.0)

    assert sleeps == [pytest.approx(1.5, abs=1e-6)]


def test_client_raises_on_http_error() -> None:
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    mock_session.get.return_value = mock_response

    client = PoliteHttpClient(
        config=ScraperConfig(delay_seconds=0.0),
        session=mock_session,
    )

    with pytest.raises(requests.HTTPError):
        client.get_text("https://books.toscrape.com/error")
