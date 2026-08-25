from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from src.exceptions import CreditRequestPersistenceError
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
    repository = CreditRequestRepository(tmp_path / "missing.csv", retry_attempts=1)
    with pytest.raises(CreditRequestPersistenceError):
        repository.save(_credit_request())


def test_credit_request_repository_retries_permission_error(tmp_path: Path) -> None:
    path = tmp_path / "requests.csv"
    path.write_text(
        "cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido\n",
        encoding="utf-8",
    )
    repository = CreditRequestRepository(
        path,
        retry_attempts=3,
        retry_delay_seconds=0,
    )
    real_open = Path.open
    attempts = {"count": 0}

    def flaky_open(self, *args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise PermissionError(13, "Permission denied", str(self))
        return real_open(self, *args, **kwargs)

    with patch.object(Path, "open", flaky_open):
        repository.save(_credit_request())

    rows = path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2
    assert attempts["count"] == 3


def test_credit_request_repository_does_not_duplicate_on_retry(tmp_path: Path) -> None:
    path = tmp_path / "requests.csv"
    path.write_text(
        "cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido\n",
        encoding="utf-8",
    )
    repository = CreditRequestRepository(path, retry_attempts=3, retry_delay_seconds=0)
    real_open = Path.open
    attempts = {"count": 0}

    def flaky_open(self, *args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise PermissionError(13, "Permission denied", str(self))
        return real_open(self, *args, **kwargs)

    with patch.object(Path, "open", flaky_open):
        repository.save(_credit_request())

    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_credit_request_repository_raises_after_retry_exhaustion(tmp_path: Path) -> None:
    path = tmp_path / "requests.csv"
    path.write_text(
        "cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido\n",
        encoding="utf-8",
    )
    repository = CreditRequestRepository(path, retry_attempts=2, retry_delay_seconds=0)

    with (
        patch.object(Path, "open", side_effect=PermissionError(13, "locked", str(path))),
        pytest.raises(CreditRequestPersistenceError),
    ):
        repository.save(_credit_request())

    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_credit_request_repository_wraps_os_error(tmp_path: Path) -> None:
    path = tmp_path / "requests.csv"
    path.write_text(
        "cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido\n",
        encoding="utf-8",
    )
    repository = CreditRequestRepository(path, retry_attempts=1)

    with (
        patch.object(Path, "open", side_effect=OSError("disk unavailable")),
        pytest.raises(CreditRequestPersistenceError),
    ):
        repository.save(_credit_request())


def _credit_request() -> CreditRequest:
    return CreditRequest(
        cpf_cliente="1",
        data_hora_solicitacao=datetime(2026, 1, 1, tzinfo=UTC),
        limite_atual=1000,
        novo_limite_solicitado=2000,
        status_pedido="pendente",
    )
