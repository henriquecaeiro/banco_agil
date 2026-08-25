import logging
from typing import ClassVar

import httpx

logger = logging.getLogger(__name__)


class ExchangeService:
    supported_currencies: ClassVar = {"USD", "EUR", "GBP", "ARS", "JPY"}

    def __init__(self, base_url: str, client: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=8.0)

    def quote_in_brl(self, currency: str) -> float:
        currency = currency.upper()
        if currency not in self.supported_currencies:
            raise ValueError("Moeda não suportada.")
        try:
            response = self.client.get(f"{self.base_url}/{currency}")
            response.raise_for_status()
            payload = response.json()
            rate = payload.get("rates", {}).get("BRL")
            if not isinstance(rate, (int, float)):
                raise TypeError("Resposta de câmbio inesperada.")
            return float(rate)
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as error:
            logger.warning("Exchange API failed: %s", error)
            raise ConnectionError("Não foi possível consultar o câmbio agora.") from error
