from src.agents.decisions import AgentDecision, intent_to_action
from src.agents.profiles import EXCHANGE_PROFILE
from src.services.exchange_service import ExchangeService
from src.tools.currency import (
    CURRENCY_DISPLAY_NAMES,
    KNOWN_CURRENCY_CODES,
    CurrencyMatch,
    identify_currency,
    unidentified_currency_message,
    unsupported_currency_message,
)
from src.tools.intents import deterministic_intent


class ExchangeAgent:
    """Especialista em câmbio: interpreta a moeda e consulta a API somente se permitida."""

    profile = EXCHANGE_PROFILE

    def __init__(self, exchange_service: ExchangeService, decision_service=None):
        self.exchange_service = exchange_service
        self.decision_service = decision_service

    def decide(self, message: str) -> AgentDecision:
        if self.decision_service is None:
            return AgentDecision(action=intent_to_action(deterministic_intent(message)))
        return self.decision_service.decide(self.profile, message)

    def respond(self, message: str, suggested_currency: str | None = None) -> str:
        match = identify_currency(message)
        if match is None:
            match = self._match_suggested_currency(suggested_currency)
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

    @staticmethod
    def _match_suggested_currency(suggested_currency: str | None) -> CurrencyMatch | None:
        if not suggested_currency:
            return None
        code = suggested_currency.upper()
        if ExchangeService.is_supported(code):
            return CurrencyMatch(
                code=code,
                display_name=CURRENCY_DISPLAY_NAMES.get(code, code),
                supported=True,
            )
        if code in KNOWN_CURRENCY_CODES:
            return CurrencyMatch(
                code=code,
                display_name=CURRENCY_DISPLAY_NAMES.get(code, code),
                supported=False,
            )
        return None
