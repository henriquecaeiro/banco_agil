from pathlib import Path
from unittest.mock import patch

import pytest

from src.exceptions import CreditRequestPersistenceError
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


def test_persists_pending_then_final_status(
    service: CreditService, customer: Customer, monkeypatch: pytest.MonkeyPatch
) -> None:
    statuses: list[str] = []
    original_save = service.request_repository.save
    original_update = service.request_repository.update_status

    def record_save(request):
        statuses.append(f"save:{request.status_pedido}")
        original_save(request)

    def record_update(request):
        statuses.append(f"update:{request.status_pedido}")
        original_update(request)

    monkeypatch.setattr(service.request_repository, "save", record_save)
    monkeypatch.setattr(service.request_repository, "update_status", record_update)

    service.request_increase(customer, "4000")

    assert statuses == ["save:pendente", "update:aprovado"]


def test_keeps_pending_request_when_analysis_fails(
    service: CreditService, customer: Customer, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail_analysis(score: int):
        raise ValueError("score indisponível")

    monkeypatch.setattr(service, "maximum_limit", fail_analysis)

    with pytest.raises(ValueError, match="score indisponível"):
        service.request_increase(customer, "4000")

    persisted = (tmp_path / "requests.csv").read_text()
    assert "pendente" in persisted
    assert "aprovado" not in persisted
    assert "rejeitado" not in persisted


def test_rejects_above_score_limit(service: CreditService, customer: Customer, tmp_path: Path) -> None:
    request = service.request_increase(customer, "6000")
    assert request.status_pedido == "rejeitado"
    persisted = (tmp_path / "requests.csv").read_text()
    assert "rejeitado" in persisted
    assert "pendente" not in persisted


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


def test_propagates_persistence_error_without_partial_save(
    service: CreditService, customer: Customer, tmp_path: Path
) -> None:
    with (
        patch.object(
            service.request_repository,
            "save",
            side_effect=CreditRequestPersistenceError("locked"),
        ),
        pytest.raises(CreditRequestPersistenceError),
    ):
        service.request_increase(customer, "4000")

    persisted = (tmp_path / "requests.csv").read_text().splitlines()
    assert len(persisted) == 1


@pytest.mark.parametrize("value", ["R$ 150.000", "R$ 150.000,00", "150000"])
def test_accepts_high_credit_request_values(
    service: CreditService, customer: Customer, value: str
) -> None:
    request = service.request_increase(customer, value)
    assert request.novo_limite_solicitado == 150000
