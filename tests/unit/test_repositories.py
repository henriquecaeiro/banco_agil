from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.models import CreditRequest
from src.repositories import CreditRequestRepository, CustomerRepository


def test_customer_repository_reads_and_updates_only_target(tmp_path: Path) -> None:
    path = tmp_path / "clientes.csv"
    path.write_text(
        "cpf,nome,data_nascimento,score,limite_credito\n"
        "1,Ana,1990-01-01,500,1000\n"
        "2,Bia,1991-01-01,600,2000\n",
        encoding="utf-8",
    )
    repository = CustomerRepository(path)

    assert repository.find_by_cpf("1").nome == "Ana"
    updated = repository.update_score("1", 750)

    assert updated.score == 750
    assert repository.find_by_cpf("2").score == 600


def test_customer_repository_handles_missing_customer_and_file(tmp_path: Path) -> None:
    missing = CustomerRepository(tmp_path / "missing.csv")
    with pytest.raises(FileNotFoundError):
        missing.find_by_cpf("1")

    path = tmp_path / "clientes.csv"
    path.write_text(
        "cpf,nome,data_nascimento,score,limite_credito\n1,Ana,1990-01-01,500,1000\n",
        encoding="utf-8",
    )
    repository = CustomerRepository(path)
    assert repository.find_by_cpf("9") is None
    with pytest.raises(LookupError):
        repository.update_score("9", 700)


def test_credit_request_repository_writes_and_updates(tmp_path: Path) -> None:
    path = tmp_path / "requests.csv"
    path.write_text(
        "cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido\n",
        encoding="utf-8",
    )
    repository = CreditRequestRepository(path)
    pending = _credit_request()

    repository.save(pending)
    repository.update_status(pending.model_copy(update={"status_pedido": "aprovado"}))

    assert "aprovado" in path.read_text(encoding="utf-8")


def test_credit_request_repository_requires_existing_file(tmp_path: Path) -> None:
    repository = CreditRequestRepository(tmp_path / "missing.csv")
    with pytest.raises(FileNotFoundError):
        repository.save(_credit_request())


def _credit_request() -> CreditRequest:
    return CreditRequest(
        cpf_cliente="1",
        data_hora_solicitacao=datetime(2026, 1, 1, tzinfo=UTC),
        limite_atual=1000,
        novo_limite_solicitado=2000,
        status_pedido="pendente",
    )
