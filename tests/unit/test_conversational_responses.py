import pytest

from src.tools.authentication import looks_like_birth_date_input
from src.tools.responses import unsupported_intent_message


@pytest.mark.parametrize(
    "value",
    ["15/05/1990", "1990-05-15", "5/5/1990"],
)
def test_recognizes_birth_date_formats(value: str) -> None:
    assert looks_like_birth_date_input(value)


@pytest.mark.parametrize(
    "value",
    ["Quanto está o dólar?", "banana", "ontem"],
)
def test_rejects_non_date_inputs(value: str) -> None:
    assert not looks_like_birth_date_input(value)


def test_unsupported_intent_messages_are_domain_safe() -> None:
    assert "Não consigo ajudar" in unsupported_intent_message("Faça uma receita de bolo.")
    assert "não consigo realizar" in unsupported_intent_message("Quero fazer um PIX.").lower()
    assert "Banco Ágil" in unsupported_intent_message("Você usa Gemini?")
