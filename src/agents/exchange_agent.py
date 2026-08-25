import re
from typing import ClassVar

from src.services.exchange_service import ExchangeService


class ExchangeAgent:
    supported_aliases: ClassVar[dict[str, str]] = {
        "dólar": "USD",
        "dolar": "USD",
        "usd": "USD",
        "euro": "EUR",
        "eur": "EUR",
        "libra": "GBP",
        "gbp": "GBP",
        "peso": "ARS",
        "ars": "ARS",
        "iene": "JPY",
        "jpy": "JPY",
    }
    unsupported_aliases: ClassVar[dict[str, str]] = {
        "canadense": "CAD",
        "cad": "CAD",
        "chf": "CHF",
        "suíço": "CHF",
        "suico": "CHF",
        "suíça": "CHF",
        "suica": "CHF",
        "franco": "CHF",
    }
    unsupported_phrases: ClassVar[tuple[str, ...]] = (
        "dólar canadense",
        "dolar canadense",
        "franco suíço",
        "franco suico",
    )

    def __init__(self, exchange_service: ExchangeService):
        self.exchange_service = exchange_service

    def respond(self, message: str) -> str:
        identification = self._identify_currency(message)
        if identification is None:
            return "Informe a moeda que deseja consultar, por exemplo dólar ou euro."

        currency, supported = identification
        if not supported:
            return (
                f"No momento não consigo consultar {currency}. "
                f"Posso consultar {ExchangeService.format_supported_currencies()}."
            )

        try:
            rate = self.exchange_service.quote_in_brl(currency)
        except ConnectionError:
            return "Não consegui consultar a cotação neste momento. Podemos tentar novamente?"
        except (TypeError, ValueError):
            return "Não consegui consultar a cotação neste momento. Podemos tentar novamente?"
        return f"A cotação de 1 {currency} é R$ {rate:.2f}. Posso ajudar com outra informação?"

    def _identify_currency(self, message: str) -> tuple[str, bool] | None:
        text = message.lower()

        for phrase in self.unsupported_phrases:
            if phrase in text:
                return ("CAD", False) if "canad" in phrase else ("CHF", False)

        for match in re.finditer(r"\b([a-z]{3})\b", text):
            code = match.group(1).upper()
            if ExchangeService.is_supported(code):
                return code, True
            if code in {"CAD", "CHF"}:
                return code, False

        words = set(re.findall(r"[a-zá-ú]+", text))

        for alias, code in self.unsupported_aliases.items():
            if alias in words:
                return code, False

        for alias, code in self.supported_aliases.items():
            if alias in words:
                return code, True

        return None
