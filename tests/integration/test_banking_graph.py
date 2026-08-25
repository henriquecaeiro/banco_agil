from pathlib import Path

from src.graph import BankingGraph


def test_authenticated_customer_can_request_credit(tmp_path: Path) -> None:
    (tmp_path / "clientes.csv").write_text(
        "cpf,nome,data_nascimento,score,limite_credito\n11144477735,Ana,1990-05-15,780,5000\n"
    )
    (tmp_path / "score_limite.csv").write_text("score_min,score_max,limite_maximo\n0,1000,10000\n")
    (tmp_path / "solicitacoes_aumento_limite.csv").write_text(
        "cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido\n"
    )
    graph, state = BankingGraph(tmp_path), {}
    state = graph.invoke(state, "111.444.777-35")
    state = graph.invoke(state, "15/05/1990")
    state = graph.invoke(state, "quero aumento de limite")
    state = graph.invoke(state, "8000")
    assert "aprovado" in state["response"]
