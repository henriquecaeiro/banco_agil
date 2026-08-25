from pathlib import Path

import pytest

from src.agents import TriageAgent
from src.repositories import CustomerRepository
from src.tools.authentication import normalize_cpf


@pytest.fixture
def repository(tmp_path: Path) -> CustomerRepository:
    file = tmp_path / "clientes.csv"
    file.write_text(
        "cpf,nome,data_nascimento,score,limite_credito\n11144477735,Ana,1990-05-15,780,5000\n",
        encoding="utf-8",
    )
    return CustomerRepository(file)


def test_normalizes_cpf() -> None:
    assert normalize_cpf("111.444.777-35") == "11144477735"


def test_authenticates_correct_customer(repository: CustomerRepository) -> None:
    state: dict = {}
    response = TriageAgent(repository).authenticate(state, "111.444.777-35", "15/05/1990")
    assert "confirmada" in response
    assert state["authenticated"] is True


def test_rejects_incorrect_birth_date(repository: CustomerRepository) -> None:
    state: dict = {}
    TriageAgent(repository).authenticate(state, "11144477735", "1990-05-16")
    assert state["authentication_attempts"] == 1
    assert not state.get("authenticated")


def test_ends_after_three_failures(repository: CustomerRepository) -> None:
    state: dict = {}
    agent = TriageAgent(repository)
    for _ in range(3):
        response = agent.authenticate(state, "000", "2000-01-01")
    assert "encerrei" in response
    assert state["conversation_ended"] is True
