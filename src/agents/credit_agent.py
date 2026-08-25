from src.agents.decisions import AgentDecision, intent_to_action
from src.agents.profiles import CREDIT_PROFILE
from src.models import Customer
from src.services.credit_service import CreditService
from src.tools.intents import deterministic_intent


class CreditAgent:
    """Especialista em limite: interpreta o pedido e executa regras de crédito determinísticas."""

    profile = CREDIT_PROFILE

    def __init__(self, credit_service: CreditService, decision_service=None):
        self.credit_service = credit_service
        self.decision_service = decision_service

    def decide(self, message: str) -> AgentDecision:
        if self.decision_service is None:
            return AgentDecision(action=intent_to_action(deterministic_intent(message)))
        return self.decision_service.decide(self.profile, message)

    def consult_limit(self, customer_data: dict) -> str:
        customer = Customer(**customer_data)
        return (
            f"Seu limite de crédito atual é R$ {self.credit_service.current_limit(customer):.2f}."
        )

    def request_increase(self, customer_data: dict, value: str) -> tuple[str, str]:
        customer = Customer(**customer_data)
        request = self.credit_service.request_increase(customer, value)
        if request.status_pedido == "aprovado":
            return ("Seu aumento de limite foi aprovado.", "credit")
        return (
            "Não foi possível aprovar o limite solicitado considerando seu score atual. Deseja fazer uma entrevista financeira?",
            "offer_interview",
        )
