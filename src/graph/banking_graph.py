from pathlib import Path

from langgraph.graph import END, START, StateGraph

from src.agents import CreditAgent, CreditInterviewAgent, ExchangeAgent, TriageAgent
from src.config.settings import settings
from src.graph.state import BankingState
from src.repositories import CreditRequestRepository, CustomerRepository
from src.services import CreditService, CustomerService, ExchangeService, IntentService
from src.services.intent_service import deterministic_intent
from src.tools.authentication import normalize_cpf
from src.tools.conversation import end_conversation


class BankingGraph:
    def __init__(
        self,
        data_dir: Path | None = None,
        exchange_service: ExchangeService | None = None,
        intent_service: IntentService | None = None,
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
        self.intent_service = intent_service or IntentService(
            api_key=settings.gemini_api_key, model=settings.llm_model
        )
        self.graph = self._compile()

    def _compile(self):
        graph = StateGraph(BankingState)
        graph.add_node("route", self._route_entry)
        graph.add_node("closed", self._closed)
        graph.add_node("authenticate", self._authenticate_node)
        graph.add_node("end_conversation", self._end)
        graph.add_node("answer_interview", self._answer_interview)
        graph.add_node("analyze_credit_request", self._analyze_credit_request)
        graph.add_node("handle_interview_offer", self._handle_interview_offer)
        graph.add_node("identify_intent", self._identify_intent)
        graph.add_node("consult_limit", self._consult_limit)
        graph.add_node("request_increase", self._request_increase)
        graph.add_node("start_interview", self._start_interview)
        graph.add_node("quote_exchange", self._quote_exchange)
        graph.add_node("unsupported", self._unsupported)

        graph.add_edge(START, "route")
        graph.add_conditional_edges(
            "route",
            self._select_route,
            {
                "closed": "closed",
                "authenticate": "authenticate",
                "end": "end_conversation",
                "interview": "answer_interview",
                "credit_request": "analyze_credit_request",
                "interview_offer": "handle_interview_offer",
                "intent": "identify_intent",
            },
        )
        graph.add_conditional_edges(
            "identify_intent",
            self._select_intent,
            {
                "limit": "consult_limit",
                "increase": "request_increase",
                "interview": "start_interview",
                "exchange": "quote_exchange",
                "end": "end_conversation",
                "unsupported": "unsupported",
            },
        )
        for node in (
            "closed",
            "authenticate",
            "end_conversation",
            "answer_interview",
            "analyze_credit_request",
            "handle_interview_offer",
            "consult_limit",
            "request_increase",
            "start_interview",
            "quote_exchange",
            "unsupported",
        ):
            graph.add_edge(node, END)
        return graph.compile()

    def invoke(self, state: BankingState, message: str) -> BankingState:
        current = dict(state)
        current.setdefault("messages", [])
        current["message"] = message
        current["messages"].append({"role": "user", "content": message})
        result = self.graph.invoke(current)
        result["messages"].append({"role": "assistant", "content": result["response"]})
        return result

    @staticmethod
    def _route_entry(state: BankingState) -> dict:
        return {}

    @staticmethod
    def _select_route(state: BankingState) -> str:
        message = state["message"].strip()
        if state.get("conversation_ended"):
            return "closed"
        if not state.get("authenticated"):
            return "authenticate"
        if deterministic_intent(message) == "end":
            return "end"
        current_agent = state.get("current_agent")
        if current_agent == "interview":
            return "interview"
        if current_agent == "awaiting_limit":
            return "credit_request"
        if current_agent == "offer_interview":
            return "interview_offer"
        return "intent"

    @staticmethod
    def _select_intent(state: BankingState) -> str:
        return state.get("intent", "unsupported")

    @staticmethod
    def _closed(state: BankingState) -> BankingState:
        state["response"] = "Este atendimento já foi encerrado. Reinicie para começar novamente."
        return state

    def _authenticate_node(self, state: BankingState) -> BankingState:
        return self._authenticate(state, state["message"].strip())

    @staticmethod
    def _end(state: BankingState) -> BankingState:
        end_conversation(state)
        state["response"] = "Atendimento encerrado. Obrigado por falar com o Banco Ágil!"
        return state

    def _answer_interview(self, state: BankingState) -> BankingState:
        try:
            state["response"], completed = self.interview.answer(state, state["message"].strip())
            if completed:
                state["current_agent"] = "credit"
        except ValueError as error:
            state["response"] = str(error)
        return state

    def _analyze_credit_request(self, state: BankingState) -> BankingState:
        try:
            state["response"], next_agent = self.credit.request_increase(
                state["customer"], state["message"].strip()
            )
            state["current_agent"] = next_agent
        except ValueError as error:
            state["response"] = str(error)
        return state

    def _handle_interview_offer(self, state: BankingState) -> BankingState:
        answer = state["message"].strip().lower()
        if answer in {"sim", "s"}:
            state["current_agent"] = "interview"
            state["response"] = self.interview.start(state)
        elif answer in {"não", "nao", "n"}:
            state["current_agent"] = None
            state["response"] = (
                "Tudo bem. Posso ajudar com outro atendimento ou encerrar quando desejar."
            )
        else:
            state["response"] = "Deseja fazer a entrevista financeira? Responda sim ou não."
        return state

    def _identify_intent(self, state: BankingState) -> BankingState:
        state["intent"] = self.intent_service.classify(state["message"].strip())
        return state

    def _consult_limit(self, state: BankingState) -> BankingState:
        state["current_agent"] = "credit"
        state["response"] = self.credit.consult_limit(state["customer"])
        return state

    @staticmethod
    def _request_increase(state: BankingState) -> BankingState:
        state["current_agent"] = "awaiting_limit"
        state["response"] = "Qual novo limite você deseja solicitar?"
        return state

    def _start_interview(self, state: BankingState) -> BankingState:
        state["current_agent"] = "interview"
        state["response"] = self.interview.start(state)
        return state

    def _quote_exchange(self, state: BankingState) -> BankingState:
        state["current_agent"] = "exchange"
        state["response"] = self.exchange.respond(state["message"])
        return state

    @staticmethod
    def _unsupported(state: BankingState) -> BankingState:
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
