from src.agents.decisions import AgentDecision
from src.agents.profiles import TRIAGE_PROFILE
from src.repositories import CustomerRepository
from src.services.intent_service import AgentDecisionService, deterministic_intent
from src.tools.authentication import authenticate_customer, normalize_cpf
from src.tools.conversation import end_conversation


class TriageAgent:
    """Porta de entrada: autentica de forma determinística e interpreta a necessidade."""

    profile = TRIAGE_PROFILE

    def __init__(
        self,
        customer_repository: CustomerRepository,
        decision_service: AgentDecisionService | None = None,
    ):
        self.customer_repository = customer_repository
        self.decision_service = decision_service

    def greeting(self) -> str:
        return "Olá! Bem-vindo ao Banco Ágil. Para começarmos, poderia informar seu CPF?"

    def decide(self, message: str) -> AgentDecision:
        if self.decision_service is None:
            from src.agents.decisions import intent_to_action

            return AgentDecision(action=intent_to_action(deterministic_intent(message)))
        return self.decision_service.decide(self.profile, message)

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
