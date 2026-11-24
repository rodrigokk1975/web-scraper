"""Cliente HTTP educado com User-Agent, retries e rate limiting."""

from __future__ import annotations

import logging
import time
from typing import Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from web_scraper.config import ScraperConfig

logger = logging.getLogger(__name__)


class PoliteHttpClient:
    """Wrapper sobre requests.Session com backoff exponencial e intervalo mínimo."""

    def __init__(
        self,
        config: ScraperConfig,
        session: requests.Session | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        clock_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config
        self._sleep = sleep_fn
        self._clock = clock_fn
        self._last_request_at: float | None = None
        self.session = session or self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"User-Agent": self.config.user_agent})

        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _respect_rate_limit(self, effective_delay: float) -> None:
        if effective_delay <= 0 or self._last_request_at is None:
            return
        elapsed = self._clock() - self._last_request_at
        remaining = effective_delay - elapsed
        if remaining > 0:
            logger.debug("Aguardando %.2fs para respeitar o rate limit.", remaining)
            self._sleep(remaining)

    def get_text(self, url: str, min_delay: float | None = None) -> str:
        """Executa GET respeitando o delay configurado e retorna o corpo HTML em texto."""
        effective_delay = max(self.config.delay_seconds, min_delay or 0.0)
        self._respect_rate_limit(effective_delay)

        logger.debug("Requisitando URL: %s", url)
        response = self.session.get(url, timeout=self.config.timeout_seconds)
        self._last_request_at = self._clock()
        response.raise_for_status()

        if response.encoding is None or response.encoding.lower() == "iso-8859-1":
            response.encoding = "utf-8"
        return response.text

    def close(self) -> None:
        """Fecha a sessão HTTP subjacente."""
        self.session.close()

    def __enter__(self) -> PoliteHttpClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
