import re

from src.services.exchange_service import ExchangeService


class ExchangeAgent:
    aliases = {
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

    def __init__(self, exchange_service: ExchangeService):
        self.exchange_service = exchange_service

    def respond(self, message: str) -> str:
        words = set(re.findall(r"[a-zá-ú]+", message.lower()))
        currency = next((code for alias, code in self.aliases.items() if alias in words), None)
        if not currency:
            return "Informe a moeda que deseja consultar, por exemplo dólar ou euro."
        try:
            rate = self.exchange_service.quote_in_brl(currency)
        except (ConnectionError, ValueError):
            return "Não consegui consultar essa cotação agora. Podemos tentar novamente?"
        return f"A cotação de 1 {currency} é R$ {rate:.2f}. Posso ajudar com outra informação?"
