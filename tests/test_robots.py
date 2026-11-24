"""Testes unitários para o módulo robots."""

from __future__ import annotations

from unittest.mock import MagicMock

import requests

from web_scraper.robots import RobotsChecker


def test_robots_allows_and_disallows_paths() -> None:
    checker = RobotsChecker(
        base_url="https://books.toscrape.com/",
        user_agent="EducationalWebScraper/0.1",
    )
    checker.load_from_text(
        "User-agent: *\n"
        "Disallow: /private/\n"
        "Allow: /catalogue/\n"
        "Crawl-delay: 2\n"
    )

    assert checker.can_fetch("https://books.toscrape.com/catalogue/page-1.html") is True
    assert checker.can_fetch("https://books.toscrape.com/private/secret.html") is False
    assert checker.crawl_delay() == 2.0


def test_robots_404_allows_fetching_by_default() -> None:
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.get.return_value = mock_response

    checker = RobotsChecker(
        base_url="https://books.toscrape.com/",
        user_agent="EducationalWebScraper/0.1",
        session=mock_session,
    )

    assert checker.can_fetch("https://books.toscrape.com/index.html") is True
    assert checker.crawl_delay() is None


def test_robots_403_disallows_fetching() -> None:
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_session.get.return_value = mock_response

    checker = RobotsChecker(
        base_url="https://books.toscrape.com/",
        user_agent="EducationalWebScraper/0.1",
        session=mock_session,
    )

    assert checker.can_fetch("https://books.toscrape.com/index.html") is False


def test_robots_network_error_fails_closed() -> None:
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.ConnectionError("offline")

    checker = RobotsChecker(
        base_url="https://books.toscrape.com/",
        user_agent="EducationalWebScraper/0.1",
        session=mock_session,
    )

    assert checker.can_fetch("https://books.toscrape.com/index.html") is False
