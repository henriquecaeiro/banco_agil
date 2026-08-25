import pytest

from src.ui.chat_processing import (
    DEFAULT_LOADING_MESSAGE,
    GENERIC_ERROR_MESSAGE,
    process_chat_turn,
    resolve_loading_message,
    run_with_processing_flag,
)


def test_processing_flag_starts_false() -> None:
    processing = False
    assert processing is False


def test_processing_flag_is_set_during_operation() -> None:
    states: list[bool] = []

    def set_processing(value: bool) -> None:
        states.append(value)

    def operation() -> str:
        states.append(True)
        return "ok"

    result = run_with_processing_flag(set_processing, operation)

    assert result == "ok"
    assert states == [True, True, False]


def test_processing_flag_is_restored_after_success() -> None:
    state = {"processing": False}

    run_with_processing_flag(
        lambda value: state.__setitem__("processing", value),
        lambda: "ok",
    )

    assert state["processing"] is False


def test_processing_flag_is_restored_after_exception() -> None:
    state = {"processing": False}

    with pytest.raises(RuntimeError, match="boom"):
        run_with_processing_flag(
            lambda value: state.__setitem__("processing", value),
            lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )

    assert state["processing"] is False


def test_resolve_loading_message_for_authentication() -> None:
    assert resolve_loading_message({}, "11144477735") == "Verificando seus dados..."


def test_resolve_loading_message_for_credit_request() -> None:
    state = {"authenticated": True, "current_agent": "awaiting_limit"}
    assert resolve_loading_message(state, "150000") == "Analisando sua solicitação..."


def test_resolve_loading_message_for_interview() -> None:
    state = {"authenticated": True, "current_agent": "interview"}
    assert resolve_loading_message(state, "9000") == "Atualizando sua análise de crédito..."


def test_resolve_loading_message_for_exchange() -> None:
    state = {"authenticated": True}
    assert resolve_loading_message(state, "Quanto está o euro?") == "Consultando a cotação..."


def test_resolve_loading_message_default() -> None:
    state = {"authenticated": True, "current_agent": "credit"}
    assert resolve_loading_message(state, "consultar limite") == DEFAULT_LOADING_MESSAGE


class FakeGraph:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def invoke(self, state: dict, prompt: str) -> dict:
        self.calls += 1
        if self.fail:
            raise ValueError("invalid")
        return {**state, "response": f"processed:{prompt}"}


def test_process_chat_turn_returns_updated_state() -> None:
    graph = FakeGraph()
    state = {"authenticated": True}

    updated_state, response = process_chat_turn(graph, state, "quero limite")

    assert graph.calls == 1
    assert response == "processed:quero limite"
    assert updated_state["response"] == "processed:quero limite"


def test_process_chat_turn_keeps_state_on_error() -> None:
    graph = FakeGraph(fail=True)
    state = {"authenticated": True, "current_agent": "credit"}

    updated_state, response = process_chat_turn(graph, state, "quero limite")

    assert graph.calls == 1
    assert updated_state is state
    assert response == GENERIC_ERROR_MESSAGE
