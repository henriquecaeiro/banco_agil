from src.repositories import CustomerRepository
from src.tools.authentication import authenticate_customer, normalize_cpf
from src.tools.conversation import end_conversation


class TriageAgent:
    """Collects credentials and routes only after successful authentication."""

    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

    def greeting(self) -> str:
        return "Olá! Bem-vindo ao Banco Ágil. Para começarmos, poderia informar seu CPF?"

    def authenticate(self, state: dict, cpf: str, birth_date: str) -> str:
        if state.get("conversation_ended"):
            return "Este atendimento já foi encerrado. Reinicie para começar novamente."
        customer = self.customer_repository.find_by_cpf(normalize_cpf(cpf))
        if authenticate_customer(customer, birth_date):
            state.update(
                authenticated=True, customer=customer.model_dump(), authentication_attempts=0
            )
            return f"Identidade confirmada, {customer.nome.split()[0]}. Como posso ajudar?"
        state["authentication_attempts"] = state.get("authentication_attempts", 0) + 1
        if state["authentication_attempts"] >= 3:
            end_conversation(state)
            return "Não foi possível confirmar sua identidade após três tentativas. Por segurança, encerrei este atendimento."
        remaining = 3 - state["authentication_attempts"]
        return f"Não consegui confirmar os dados. Você ainda tem {remaining} tentativa(s). Informe CPF e data de nascimento novamente."
