import csv
from pathlib import Path

import httpx

from src.graph import BankingGraph
from src.services import ExchangeService, IntentService
from src.tools.responses import (
    AUTH_BIRTH_DATE_MESSAGE,
    AUTH_REQUIRED_MESSAGE,
    BANKING_UNAVAILABLE_MESSAGE,
    OUT_OF_SCOPE_MESSAGE,
)


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


def build_graph(tmp_path: Path) -> BankingGraph:
    exchange = ExchangeService(
        "https://example.test",
        httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"rates": {"BRL": 5.5}})
            )
        ),
    )
    return BankingGraph(tmp_path, exchange_service=exchange, intent_service=IntentService())


def authenticate(graph: BankingGraph, state: dict | None = None) -> dict:
    state = state or {}
    state = graph.invoke(state, "11144477735")
    return graph.invoke(state, "15/05/1990")


def test_kwanza_is_recognized_as_unsupported_currency(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph = build_graph(tmp_path)
    state = authenticate(graph)

    state = graph.invoke(state, "Quanto está o kwanza hoje?")

    assert "AOA" in state["response"]
    assert "não consigo consultar a cotação" in state["response"].lower()


def test_off_topic_request_gets_domain_safe_response(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph = build_graph(tmp_path)
    state = authenticate(graph)

    state = graph.invoke(state, "Faça uma receita de bolo.")

    assert state["response"] == OUT_OF_SCOPE_MESSAGE


def test_banking_out_of_scope_gets_specific_response(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph = build_graph(tmp_path)
    state = authenticate(graph)

    state = graph.invoke(state, "Quero fazer um PIX.")

    assert state["response"] == BANKING_UNAVAILABLE_MESSAGE


def test_unauthenticated_credit_request_requires_auth(tmp_path: Path) -> None:
    setup_data(tmp_path)
    state = build_graph(tmp_path).invoke({}, "Qual é meu limite?")

    assert AUTH_REQUIRED_MESSAGE in state["response"]
    assert state.get("authenticated") is not True


def test_exchange_during_birth_date_step_does_not_consume_auth_attempt(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph = build_graph(tmp_path)
    state = graph.invoke({}, "11144477735")
    state = graph.invoke(state, "Quanto está o dólar?")

    assert state["response"] == AUTH_BIRTH_DATE_MESSAGE
    assert state.get("authentication_attempts", 0) == 0


def test_awaiting_limit_switches_to_exchange_intent(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph = build_graph(tmp_path)
    state = authenticate(graph)
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "Quanto está o dólar?")

    assert "USD" in state["response"]
    assert "5.50" in state["response"]


def test_awaiting_limit_rejects_invalid_amount(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph = build_graph(tmp_path)
    state = authenticate(graph)
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "banana")

    assert state["current_agent"] == "awaiting_limit"
    assert "valor monetário válido" in state["response"]


def test_interview_offer_accepts_natural_yes(tmp_path: Path) -> None:
    setup_data(tmp_path, score=300)
    graph = build_graph(tmp_path)
    state = authenticate(graph)
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "9000")
    state = graph.invoke(state, "claro")

    assert state["current_agent"] == "interview"
    assert "renda" in state["response"].lower()


def test_rejected_request_is_reanalyzed_after_interview(tmp_path: Path) -> None:
    setup_data(tmp_path, score=300)
    graph = build_graph(tmp_path)
    state = authenticate(graph)
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "9000")
    state = graph.invoke(state, "sim")
    for answer in ("9000", "formal", "1000", "0", "não"):
        state = graph.invoke(state, answer)

    assert "aprovado" in state["response"]
    assert state["current_agent"] == "credit"
    assert not state.get("pending_credit_request")
    with (tmp_path / "solicitacoes_aumento_limite.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert [row["status_pedido"] for row in rows] == ["rejeitado", "aprovado"]


def test_reanalysis_does_not_offer_interview_loop(tmp_path: Path) -> None:
    setup_data(tmp_path, score=300)
    graph = build_graph(tmp_path)
    state = authenticate(graph)
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "9000")
    state = graph.invoke(state, "sim")
    for answer in ("1000", "desempregado", "5000", "3", "sim"):
        state = graph.invoke(state, answer)

    assert "aprovado" not in state["response"]
    assert "Deseja fazer uma entrevista financeira?" not in state["response"]
    assert state["current_agent"] == "credit"
