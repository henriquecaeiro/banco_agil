import pytest

from src.tools.intents import deterministic_intent


@pytest.mark.parametrize(
    "message",
    [
        "queria um limite um pouco maior",
        "queria um limite maior",
        "queria que meu limite fosse maior",
        "preciso de mais limite",
        "preciso de mais crédito",
        "dá pra aumentar o que o banco libera?",
        "tem como liberar um limite maior?",
        "consigo um pouco mais de limite?",
    ],
)
def test_natural_increase_phrases(message: str) -> None:
    assert deterministic_intent(message) == "increase"


@pytest.mark.parametrize(
    "message",
    [
        "quanto é meu limite?",
        "qual meu limite atual?",
        "quero consultar meu limite",
        "quanto o banco libera pra mim hoje?",
    ],
)
def test_natural_consult_phrases(message: str) -> None:
    assert deterministic_intent(message) == "limit"


def test_ambiguous_credit_phrase_asks_for_clarification() -> None:
    assert deterministic_intent("meu limite") == "clarify_limit"


@pytest.mark.parametrize(
    "message",
    [
        "encerrar",
        "finalizar",
        "tchau",
        "deixa pra lá",
        "não quero continuar",
        "nao quero continuar",
        "quero encerrar",
        "não quero mais continuar",
    ],
)
def test_natural_end_phrases(message: str) -> None:
    assert deterministic_intent(message) == "end"
