import csv
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from src.exceptions import CreditRequestPersistenceError
from src.graph import BankingGraph
from src.graph.banking_graph import CREDIT_ANALYSIS_UNAVAILABLE_MESSAGE
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


def build_test_graph(
    directory: Path, exchange_service: ExchangeService | None = None
) -> BankingGraph:
    return BankingGraph(
        directory,
        exchange_service=exchange_service,
        intent_service=IntentService(),
    )


def test_authenticated_customer_can_request_credit(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = build_test_graph(tmp_path), {}
    state = graph.invoke(state, "111.444.777-35")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "8000")
    assert "aprovado" in state["response"]


def test_formatted_high_credit_request_reaches_rejection_and_persists(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = build_test_graph(tmp_path), {}
    for message in ("11144477735", "15/05/1990", "quero aumento de limite"):
        state = graph.invoke(state, message)

    state = graph.invoke(state, "R$ 150.000")

    assert state["current_agent"] == "offer_interview"
    assert "entrevista financeira" in state["response"]
    with (tmp_path / "solicitacoes_aumento_limite.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 1
    assert rows[0]["novo_limite_solicitado"] == "150000"
    assert rows[0]["status_pedido"] == "rejeitado"


@pytest.mark.parametrize("amount", ["R$ 150.000,00", "150000"])
def test_high_credit_request_formats_persist_and_analyze(tmp_path: Path, amount: str) -> None:
    setup_data(tmp_path)
    graph, state = build_test_graph(tmp_path), {}
    for message in ("11144477735", "15/05/1990", "quero aumento de limite"):
        state = graph.invoke(state, message)

    state = graph.invoke(state, amount)

    assert state["current_agent"] == "offer_interview"
    with (tmp_path / "solicitacoes_aumento_limite.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 1
    assert rows[0]["novo_limite_solicitado"] in {"150000", "150000.00"}


def test_persistence_failure_keeps_retry_flow(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = build_test_graph(tmp_path), {}
    for message in ("11144477735", "15/05/1990", "quero aumento de limite"):
        state = graph.invoke(state, message)

    repository = graph.credit.credit_service.request_repository
    with patch.object(repository, "save", side_effect=CreditRequestPersistenceError("locked")):
        state = graph.invoke(state, "R$ 150.000")

    assert state["current_agent"] == "awaiting_limit"
    assert "registrar sua solicitação" in state["response"]
    with (tmp_path / "solicitacoes_aumento_limite.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        assert list(csv.DictReader(file)) == []


def test_credit_request_succeeds_after_persistence_failure(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = build_test_graph(tmp_path), {}
    for message in ("11144477735", "15/05/1990", "quero aumento de limite"):
        state = graph.invoke(state, message)

    repository = graph.credit.credit_service.request_repository
    real_save = repository.save
    attempts = {"count": 0}

    def flaky_save(request):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise CreditRequestPersistenceError("locked")
        real_save(request)

    with patch.object(repository, "save", side_effect=flaky_save):
        state = graph.invoke(state, "R$ 150.000")
        assert state["current_agent"] == "awaiting_limit"

    state = graph.invoke(state, "R$ 150.000")
    assert state["current_agent"] == "offer_interview"
    with (tmp_path / "solicitacoes_aumento_limite.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 1
    assert rows[0]["novo_limite_solicitado"] == "150000"


def test_invalid_credit_amount_stays_in_retry_flow_without_persistence(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = build_test_graph(tmp_path), {}
    for message in ("11144477735", "15/05/1990", "quero aumento de limite"):
        state = graph.invoke(state, message)

    state = graph.invoke(state, "banana")

    assert state["current_agent"] == "awaiting_limit"
    assert state["response"] == "Informe um valor monetário válido."
    with (tmp_path / "solicitacoes_aumento_limite.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        assert list(csv.DictReader(file)) == []


def test_three_authentication_failures_end_session(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = build_test_graph(tmp_path), {}
    for _ in range(3):
        state = graph.invoke(state, "11144477735")
        state = graph.invoke(state, "01/01/2000")
    assert state["conversation_ended"] is True


def test_customer_can_end_conversation_before_authentication(tmp_path: Path) -> None:
    setup_data(tmp_path)
    state = build_test_graph(tmp_path).invoke({}, "Quero encerrar.")

    assert state["conversation_ended"] is True
    assert "encerrado" in state["response"]


def test_failed_authentication_requires_a_new_cpf_before_retry(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph = build_test_graph(tmp_path)
    state = graph.invoke({}, "11144477735")
    state = graph.invoke(state, "01/01/2000")
    assert state["pending_auth_cpf"] == ""

    state = graph.invoke(state, "11144477735")
    assert "data de nascimento" in state["response"]
    state = graph.invoke(state, "15/05/1990")
    assert state["authenticated"] is True


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
    graph, state = build_test_graph(tmp_path, exchange), {}
    state = graph.invoke(state, "11144477735")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "9000")
    assert "entrevista" in state["response"]
    state = graph.invoke(state, "sim")
    for answer in ("9000", "formal", "1000", "0", "não"):
        state = graph.invoke(state, answer)
    assert "concluída" in state["response"]
    assert "aprovado" in state["response"]
    state = graph.invoke(state, "cotação do dólar")
    assert "5.50" in state["response"]


def test_customer_can_decline_credit_interview(tmp_path: Path) -> None:
    setup_data(tmp_path, score=300)
    graph, state = build_test_graph(tmp_path), {}
    for message in ("11144477735", "15/05/1990", "aumentar limite", "9000", "não"):
        state = graph.invoke(state, message)

    assert state["current_agent"] is None
    assert not state.get("pending_credit_request")
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


def test_langgraph_exposes_domain_routing_nodes(tmp_path: Path) -> None:
    setup_data(tmp_path)
    nodes = build_test_graph(tmp_path).graph.get_graph().nodes

    assert {"route", "authenticate", "identify_intent", "consult_limit", "quote_exchange"} <= set(
        nodes
    )


class SuggestedAoaDecision:
    def invoke(self, prompt: str) -> dict[str, str]:
        return {"action": "quote_exchange", "currency": "AOA"}


def test_suggested_currency_from_llm_reaches_exchange_agent(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph = BankingGraph(
        tmp_path,
        intent_service=IntentService(structured_llm=SuggestedAoaDecision()),
    )
    state = graph.invoke({}, "11144477735")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "quero a cotação daquela viagem")

    assert state["intent"] == "exchange"
    assert state["suggested_currency"] == "AOA"
    assert "AOA" in state["response"]
    assert "não consigo consultar" in state["response"].lower()


def test_fallback_increase_asks_for_new_limit(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = build_test_graph(tmp_path), {}
    state = graph.invoke(state, "11144477735")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "queria um limite um pouco maior")

    assert state["intent"] == "increase"
    assert state["current_agent"] == "awaiting_limit"


def test_ambiguous_limit_phrase_asks_consult_or_increase(tmp_path: Path) -> None:
    setup_data(tmp_path)
    graph, state = build_test_graph(tmp_path), {}
    state = graph.invoke(state, "11144477735")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "meu limite")

    assert state["intent"] == "clarify_limit"
    assert "consultar seu limite atual" in state["response"]
    assert "aumento" in state["response"]


def test_missing_score_range_uses_friendly_message(tmp_path: Path) -> None:
    (tmp_path / "clientes.csv").write_text(
        "cpf,nome,data_nascimento,score,limite_credito\n11144477735,Ana,1990-05-15,780,5000\n"
    )
    (tmp_path / "score_limite.csv").write_text(
        "score_min,score_max,limite_maximo\n0,100,500\n"
    )
    (tmp_path / "solicitacoes_aumento_limite.csv").write_text(
        "cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido\n"
    )
    graph, state = build_test_graph(tmp_path), {}
    state = graph.invoke(state, "11144477735")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "8000")

    assert state["response"] == CREDIT_ANALYSIS_UNAVAILABLE_MESSAGE
    assert "No score range found" not in state["response"]
    assert "score range" not in state["response"].lower()
    assert "ValueError" not in state["response"]
    with (tmp_path / "solicitacoes_aumento_limite.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 1
    assert rows[0]["status_pedido"] == "pendente"
