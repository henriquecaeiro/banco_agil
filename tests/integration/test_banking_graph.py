from pathlib import Path

import httpx

from src.graph import BankingGraph
from src.services import ExchangeService
from src.services.intent_service import IntentService


class NaturalLanguageIntent:
    def invoke(self, prompt: str) -> dict[str, str]:
        return {"intent": "increase"}


def setup_data(directory: Path, score: int = 780) -> None:
    (directory / "clientes.csv").write_text(
        f"cpf,nome,data_nascimento,score,limite_credito\n11144477735,Ana,1990-05-15,{score},5000\n"
    )
    (directory / "score_limite.csv").write_text(
        "score_min,score_max,limite_maximo\n0,499,2000\n500,1000,10000\n"
    )
    (directory / "solicitacoes_aumento_limite.csv").write_text(
        "cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido\n"
    )


def test_authenticated_customer_can_request_credit(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = BankingGraph(tmp_path), {}
    state = graph.invoke(state, "111.444.777-35")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "8000")
    assert "aprovado" in state["response"]


def test_three_authentication_failures_end_session(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = BankingGraph(tmp_path), {}
    for _ in range(3):
        state = graph.invoke(state, "11144477735")
        state = graph.invoke(state, "01/01/2000")
    assert state["conversation_ended"] is True


def test_rejection_interview_and_exchange_flow(tmp_path: Path) -> None:
    setup_data(tmp_path, score=300)
    exchange = ExchangeService(
        "https://example.test",
        httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"rates": {"BRL": 5.5}})
            )
        ),
    )
    graph, state = BankingGraph(tmp_path, exchange), {}
    state = graph.invoke(state, "11144477735")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "9000")
    assert "entrevista" in state["response"]
    state = graph.invoke(state, "sim")
    for answer in ("9000", "formal", "1000", "0", "não"):
        state = graph.invoke(state, answer)
    assert "concluída" in state["response"]
    state = graph.invoke(state, "cotação do dólar")
    assert "5.50" in state["response"]


def test_customer_can_decline_credit_interview(tmp_path: Path) -> None:
    setup_data(tmp_path, score=300)
    graph, state = BankingGraph(tmp_path), {}
    for message in ("11144477735", "15/05/1990", "aumentar limite", "9000", "não"):
        state = graph.invoke(state, message)

    assert state["current_agent"] is None
    assert "outro atendimento" in state["response"]


def test_structured_intent_routes_natural_language(tmp_path: Path) -> None:
    setup_data(tmp_path)
    intent_service = IntentService(structured_llm=NaturalLanguageIntent())
    graph, state = BankingGraph(tmp_path, intent_service=intent_service), {}
    state = graph.invoke(state, "11144477735")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "queria ver se consigo um limite um pouco maior")

    assert state["intent"] == "increase"
    assert state["current_agent"] == "awaiting_limit"
