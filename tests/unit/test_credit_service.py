from pathlib import Path

import pytest

from src.models import Customer
from src.repositories import CreditRequestRepository
from src.services import CreditService


@pytest.fixture
def service(tmp_path: Path) -> CreditService:
    limits = tmp_path / "limits.csv"
    limits.write_text("score_min,score_max,limite_maximo\n0,499,2000\n500,1000,5000\n")
    requests = tmp_path / "requests.csv"
    requests.write_text(
        "cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido\n"
    )
    return CreditService(limits, CreditRequestRepository(requests))


@pytest.fixture
def customer() -> Customer:
    return Customer(
        cpf="1", nome="Ana", data_nascimento="1990-01-01", score=600, limite_credito=1000
    )


def test_approves_and_persists_request(
    service: CreditService, customer: Customer, tmp_path: Path
) -> None:
    request = service.request_increase(customer, "4000")
    assert request.status_pedido == "aprovado"
    persisted = (tmp_path / "requests.csv").read_text()
    assert "aprovado" in persisted
    assert "pendente" not in persisted


def test_persists_only_final_status(
    service: CreditService, customer: Customer, monkeypatch: pytest.MonkeyPatch
) -> None:
    statuses: list[str] = []
    original_save = service.request_repository.save

    def record_save(request):
        statuses.append(request.status_pedido)
        original_save(request)

    monkeypatch.setattr(service.request_repository, "save", record_save)

    service.request_increase(customer, "4000")

    assert statuses == ["aprovado"]


def test_does_not_persist_partial_request_when_analysis_fails(
    service: CreditService, customer: Customer, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail_analysis(score: int):
        raise ValueError("score indisponível")

    monkeypatch.setattr(service, "maximum_limit", fail_analysis)

    with pytest.raises(ValueError, match="score indisponível"):
        service.request_increase(customer, "4000")

    persisted = (tmp_path / "requests.csv").read_text().splitlines()
    assert len(persisted) == 1


def test_rejects_above_score_limit(service: CreditService, customer: Customer) -> None:
    assert service.request_increase(customer, "6000").status_pedido == "rejeitado"


def test_returns_current_limit(service: CreditService, customer: Customer) -> None:
    assert service.current_limit(customer) == 1000


def test_accepts_brazilian_currency_format(service: CreditService, customer: Customer) -> None:
    request = service.request_increase(customer, "R$ 4.000,00")
    assert request.novo_limite_solicitado == 4000


@pytest.mark.parametrize("value", ["zero", "0", "-500"])
def test_rejects_invalid_request_values(
    service: CreditService, customer: Customer, value: str
) -> None:
    with pytest.raises(ValueError):
        service.request_increase(customer, value)
