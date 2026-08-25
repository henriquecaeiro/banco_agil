from typing import ClassVar

from src.models import CreditInterview
from src.services.customer_service import CustomerService


class CreditInterviewAgent:
    fields: ClassVar = (
        "renda_mensal",
        "tipo_emprego",
        "despesas_fixas_mensais",
        "numero_dependentes",
        "tem_dividas",
    )
    questions: ClassVar = {
        "renda_mensal": "Qual é sua renda mensal?",
        "tipo_emprego": "Seu tipo de emprego é formal, autônomo ou desempregado?",
        "despesas_fixas_mensais": "Quais são suas despesas fixas mensais?",
        "numero_dependentes": "Quantos dependentes você possui?",
        "tem_dividas": "Você possui dívidas ativas? Responda sim ou não.",
    }

    def __init__(self, customer_service: CustomerService):
        self.customer_service = customer_service

    def start(self, state: dict) -> str:
        state["credit_interview"] = {}
        return self.questions[self.fields[0]]

    def answer(self, state: dict, value: str) -> tuple[str, bool]:
        answers = state.setdefault("credit_interview", {})
        field = self.fields[len(answers)]
        parsed = self._parse(field, value)
        answers[field] = parsed
        if len(answers) < len(self.fields):
            return self.questions[self.fields[len(answers)]], False
        interview = CreditInterview(**answers)
        customer = self.customer_service.apply_interview(state["customer"]["cpf"], interview)
        state["customer"] = customer.model_dump()
        return (
            "Entrevista concluída. Atualizamos sua análise de crédito; você pode tentar o aumento novamente.",
            True,
        )

    @staticmethod
    def _parse(field: str, value: str):
        value = value.strip().lower()
        if field in {"renda_mensal", "despesas_fixas_mensais"}:
            try:
                result = float(value.replace(".", "").replace(",", "."))
            except ValueError as error:
                raise ValueError("Informe um valor numérico válido.") from error
            if result < 0:
                raise ValueError("O valor não pode ser negativo.")
            return result
        if field == "tipo_emprego":
            if value not in {"formal", "autônomo", "desempregado"}:
                raise ValueError("Escolha: formal, autônomo ou desempregado.")
            return value
        if field == "numero_dependentes":
            if not value.isdigit():
                raise ValueError("Informe um número inteiro de dependentes.")
            return int(value)
        if value not in {"sim", "não", "nao"}:
            raise ValueError("Responda sim ou não.")
        return value == "sim"
