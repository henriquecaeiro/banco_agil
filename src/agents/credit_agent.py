from src.models import Customer
from src.services import CreditService


class CreditAgent:
    def __init__(self, credit_service: CreditService):
        self.credit_service = credit_service

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
