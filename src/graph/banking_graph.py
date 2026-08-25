from pathlib import Path

from langgraph.graph import END, START, StateGraph

from src.agents import CreditAgent, CreditInterviewAgent, ExchangeAgent, TriageAgent
from src.config.settings import settings
from src.graph.state import BankingState
from src.repositories import CreditRequestRepository, CustomerRepository
from src.services import CreditService, CustomerService, ExchangeService
from src.tools.authentication import normalize_cpf
from src.tools.conversation import end_conversation


def _intent(message: str) -> str:
    text = message.lower()
    if any(word in text for word in ("encerrar", "finalizar", "tchau", "obrigado", "era isso")):
        return "end"
    if any(word in text for word in ("câmbio", "cambio", "dólar", "dolar", "euro", "usd", "eur")):
        return "exchange"
    if "aumento" in text or "aumentar" in text:
        return "increase"
    if "limite" in text:
        return "limit"
    if "entrevista" in text:
        return "interview"
    return "unsupported"


class BankingGraph:
    def __init__(
        self, data_dir: Path | None = None, exchange_service: ExchangeService | None = None
    ):
        directory = data_dir or settings.data_dir
        customer_repository = CustomerRepository(directory / "clientes.csv")
        self.triage = TriageAgent(customer_repository)
        self.credit = CreditAgent(
            CreditService(
                directory / "score_limite.csv",
                CreditRequestRepository(directory / "solicitacoes_aumento_limite.csv"),
            )
        )
        self.interview = CreditInterviewAgent(CustomerService(customer_repository))
        self.exchange = ExchangeAgent(
            exchange_service or ExchangeService(settings.exchange_api_url)
        )
        self.graph = self._compile()

    def _compile(self):
        graph = StateGraph(BankingState)
        graph.add_node("conversation", self._conversation)
        graph.add_edge(START, "conversation")
        graph.add_edge("conversation", END)
        return graph.compile()

    def invoke(self, state: BankingState, message: str) -> BankingState:
        current = dict(state)
        current.setdefault("messages", [])
        current["message"] = message
        current["messages"].append({"role": "user", "content": message})
        result = self.graph.invoke(current)
        result["messages"].append({"role": "assistant", "content": result["response"]})
        return result

    def _conversation(self, state: BankingState) -> BankingState:
        message = state["message"].strip()
        if state.get("conversation_ended"):
            state["response"] = (
                "Este atendimento já foi encerrado. Reinicie para começar novamente."
            )
            return state
        if not state.get("authenticated"):
            return self._authenticate(state, message)
        intent = _intent(message)
        if intent == "end":
            end_conversation(state)
            state["response"] = "Atendimento encerrado. Obrigado por falar com o Banco Ágil!"
        elif state.get("current_agent") == "interview":
            try:
                state["response"], completed = self.interview.answer(state, message)
                if completed:
                    state["current_agent"] = "credit"
            except ValueError as error:
                state["response"] = str(error)
        elif state.get("current_agent") == "awaiting_limit":
            try:
                state["response"], next_agent = self.credit.request_increase(
                    state["customer"], message
                )
                state["current_agent"] = next_agent
            except ValueError as error:
                state["response"] = str(error)
        elif state.get("current_agent") == "offer_interview" and message.lower() in {"sim", "s"}:
            state["current_agent"] = "interview"
            state["response"] = self.interview.start(state)
        elif intent == "limit":
            state["current_agent"] = "credit"
            state["response"] = self.credit.consult_limit(state["customer"])
        elif intent == "increase":
            state["current_agent"] = "awaiting_limit"
            state["response"] = "Qual novo limite você deseja solicitar?"
        elif intent == "interview":
            state["current_agent"] = "interview"
            state["response"] = self.interview.start(state)
        elif intent == "exchange":
            state["current_agent"] = "exchange"
            state["response"] = self.exchange.respond(message)
        else:
            state["response"] = (
                "Posso ajudar com limite de crédito, aumento de limite, entrevista financeira ou câmbio."
            )
        return state

    def _authenticate(self, state: BankingState, message: str) -> BankingState:
        if not state.get("pending_auth_cpf"):
            cpf = normalize_cpf(message)
            if len(cpf) != 11:
                state["response"] = "Informe um CPF válido, com 11 dígitos."
                return state
            state["pending_auth_cpf"] = cpf
            state["response"] = "Agora informe sua data de nascimento (DD/MM/AAAA)."
            return state
        state["response"] = self.triage.authenticate(state, state["pending_auth_cpf"], message)
        if (
            state.get("authenticated")
            or state.get("conversation_ended")
            or state.get("authentication_attempts")
        ):
            state.pop("pending_auth_cpf", None)
        return state


def build_banking_graph(data_dir: Path | None = None) -> BankingGraph:
    return BankingGraph(data_dir)
