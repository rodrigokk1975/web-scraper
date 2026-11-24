"""Verificação de permissões e Crawl-delay via robots.txt."""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Consulta e interpreta o robots.txt do domínio alvo."""

    def __init__(
        self,
        base_url: str,
        user_agent: str,
        timeout_seconds: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self._session = session or requests.Session()
        self._parser = RobotFileParser()
        self._loaded = False

        parsed = urlparse(base_url)
        self.robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        self._parser.set_url(self.robots_url)

    def load_from_text(self, content: str) -> None:
        """Carrega regras diretamente a partir de uma string (útil para testes)."""
        self._parser.parse(content.splitlines())
        self._loaded = True

    def load(self) -> None:
        """Baixa e interpreta o robots.txt seguindo as convenções da RFC 9309."""
        logger.info("Consultando robots.txt em %s", self.robots_url)
        try:
            response = self._session.get(
                self.robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            logger.warning(
                "Falha ao obter %s (%s). Bloqueando coleta por precaução.",
                self.robots_url,
                exc,
            )
            self._parser.disallow_all = True
            self._loaded = True
            return

        if response.status_code == 200:
            self._parser.parse(response.text.splitlines())
            logger.info("robots.txt carregado com sucesso.")
        elif response.status_code == 404:
            logger.info(
                "robots.txt não encontrado (HTTP 404). Seguindo com permissão padrão."
            )
            self._parser.allow_all = True
        elif response.status_code in (401, 403):
            logger.warning(
                "Acesso ao robots.txt negado (HTTP %s). Coleta bloqueada.",
                response.status_code,
            )
            self._parser.disallow_all = True
        else:
            logger.warning(
                "Resposta inesperada ao consultar robots.txt (HTTP %s). Coleta bloqueada.",
                response.status_code,
            )
            self._parser.disallow_all = True

        self._loaded = True

    def can_fetch(self, url: str) -> bool:
        """Retorna True se o User-Agent configurado tem permissão para acessar a URL."""
        if not self._loaded:
            self.load()
        return self._parser.can_fetch(self.user_agent, url)

    def crawl_delay(self) -> float | None:
        """Retorna o Crawl-delay (em segundos) definido no robots.txt, se houver."""
        if not self._loaded:
            self.load()
        delay = self._parser.crawl_delay(self.user_agent)
        if delay is None:
            return None
        return float(delay)
