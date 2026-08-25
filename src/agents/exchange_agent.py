from src.services.exchange_service import ExchangeService
from src.tools.currency import (
    identify_currency,
    unidentified_currency_message,
    unsupported_currency_message,
)


class ExchangeAgent:
    def __init__(self, exchange_service: ExchangeService):
        self.exchange_service = exchange_service

    def respond(self, message: str) -> str:
        match = identify_currency(message)
        if match is None:
            return unidentified_currency_message()
        if not match.supported:
            return unsupported_currency_message(match)

        try:
            rate = self.exchange_service.quote_in_brl(match.code)
        except ConnectionError:
            return "Não consegui consultar a cotação neste momento. Podemos tentar novamente?"
        except (TypeError, ValueError):
            return "Não consegui consultar a cotação neste momento. Podemos tentar novamente?"
        return (
            f"A cotação de 1 {match.code} é R$ {rate:.2f}. "
            "Posso ajudar com outra informação?"
        )
