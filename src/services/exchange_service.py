import logging
from typing import ClassVar

import httpx

logger = logging.getLogger(__name__)


class ExchangeService:
    SUPPORTED_CURRENCIES: ClassVar[frozenset[str]] = frozenset({"USD", "EUR", "GBP", "ARS", "JPY"})
    CURRENCY_LABELS: ClassVar[dict[str, str]] = {
        "USD": "dólar americano (USD)",
        "EUR": "euro (EUR)",
        "GBP": "libra esterlina (GBP)",
        "ARS": "peso argentino (ARS)",
        "JPY": "iene japonês (JPY)",
    }

    def __init__(self, base_url: str, client: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=8.0)

    @classmethod
    def is_supported(cls, currency: str) -> bool:
        return currency.upper() in cls.SUPPORTED_CURRENCIES

    @classmethod
    def format_supported_currencies(cls) -> str:
        ordered = sorted(cls.SUPPORTED_CURRENCIES)
        return ", ".join(cls.CURRENCY_LABELS[code] for code in ordered)

    def quote_in_brl(self, currency: str) -> float:
        currency = currency.upper()
        if currency not in self.SUPPORTED_CURRENCIES:
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
